import json, re, sys
sys.path.insert(0,"/home/user/daily-star-liberation-war")
from urllib.parse import urlsplit
from dstar.fetch import _cache_path
from dstar.discover import _sitemap_locs, NEWS_DESK
from dstar.store import canonical, is_priority_section, Candidates, node_id
B=r"(?:^|[/-])"; E=r"(?=$|[/-])"
STRONG=re.compile(B+r"(?:language-movement\w*|bhasha-andolon|bhasha-sainik\w*|language-martyrs?|language-heroes?|language-veterans?|language-soldiers?|state-language|rashtrabhasha|1952)"+E,re.I)
BROAD=re.compile(STRONG.pattern+"|"+B+r"(?:ekushey?|amar-ekushey?|21-february|february-21|21st-february|shaheed-minar|mother-language-day|language-day)"+E,re.I)
NOISE=re.compile(r"padak|book-fair|boi-mela|granthamela|ekushey-tv|ekushey-television|etv|bookfair|grantha-mela|vandal|cricket|budget|shaheed-minar-(?:to|for)",re.I)
def lm_topical(u):
    p=re.sub(r"-\d{4,}$","",urlsplit(u).path.rstrip("/"))
    if NOISE.search(p): return False
    first=p.split("/")[1] if p.count("/")>=1 else ""
    old=p.count("/")==1
    return bool((STRONG if (first in NEWS_DESK or old) else BROAD).search(p))
def lm_urls():
    out=set()
    for l in open("/home/user/daily-star-liberation-war/cache/fetch_log.jsonl"):
        r=json.loads(l)
        if "sitemap" in r["url"] and r.get("status")==200:
            t=open(_cache_path(r["url"])).read()
            if "<sitemapindex" in t[:3000]: continue
            for loc in _sitemap_locs(t):
                u=canonical(loc)
                if not is_priority_section(u) and lm_topical(u): out.add(u)
    return out
if __name__=="__main__":
    cands=Candidates(); urls=lm_urls()
    new=sorted(u for u in urls if node_id(u) not in cands.rows and u not in cands.rows)
    print(len(urls),"LM urls;",len(new),"new")
    if len(sys.argv)>1 and sys.argv[1]=="show": print("\n".join(new))
    if len(sys.argv)>1 and sys.argv[1]=="add":
        n=sum(cands.add(u,"sitemap:lm-slug") for u in new); cands.save(); print("added",n)
