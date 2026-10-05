"""Support for manual relevance classification.

The label for every article is assigned by a human-style reading of its text,
not by keyword counts. This module only (a) prints unlabelled articles in
batches for reading and (b) stores decisions in classification_log.csv.

Scope rule: only articles that centre on 1971 (features, analysis, opinion,
essays, memoirs, interviews, reviews) are kept. News reports -- event and
commemoration coverage ("nation observes Victory Day"), tribunal hearing or
verdict reports, anniversary notices -- are always Irrelevant, whatever the
topic, and are logged with content_type "news report" for audit.

Usage:
    python -m dstar.classify pending [N]     # show the next N unlabelled articles
    python -m dstar.classify set <node_id> <Core|Borderline|Irrelevant> <content_type> "<reason>" [--unsure "<note>"]
    python -m dstar.classify import decisions.csv   # node_id,label,content_type,reason[,unsure_note]
"""
import csv
import os
import re
import sys

from .extract import TEXT_DIR, load_records
from .store import ROOT

LOG = os.path.join(ROOT, "classification_log.csv")
FIELDS = ["url", "node_id", "label", "content_type", "reason", "unsure_note"]
LABELS = ("Core", "Borderline", "Irrelevant")
NEWS = "news report"
CONTENT_TYPES = ("feature", "analysis", "opinion", "essay", "memoir", "interview",
                 "review", "photo essay", "editorial", NEWS, "not an article", "other")
HINT = re.compile(r"1971|liberation war|muktijuddh|mukti bahini|genocide|razakar|"
                  r"freedom fighter|birangona|mujibnagar|searchlight|victory day", re.I)


def load_labels():
    labels = {}
    if os.path.exists(LOG):
        with open(LOG, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                labels[row["node_id"]] = row
    return labels


def save_labels(labels):
    tmp = LOG + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for row in labels.values():
            w.writerow({k: row.get(k, "") for k in FIELDS})
    os.replace(tmp, LOG)


def set_label(labels, recs, nid, label, content_type, reason, unsure=""):
    if label not in LABELS:
        raise SystemExit(f"bad label {label!r}")
    if content_type not in CONTENT_TYPES:
        raise SystemExit(f"bad content_type {content_type!r}; one of {CONTENT_TYPES}")
    reason = reason.strip()
    if content_type in (NEWS, "not an article") and label != "Irrelevant":
        reason = f"{content_type} (out of scope; topic would be {label}): {reason}"
        label = "Irrelevant"
    url = recs[nid]["canonical_url"] if nid in recs else ""
    labels[nid] = {"url": url, "node_id": nid, "label": label, "content_type": content_type,
                   "reason": reason, "unsure_note": unsure.strip()}


def pending(n):
    recs, labels = load_records(), load_labels()
    todo = [r for k, r in recs.items() if k not in labels]
    print(f"{len(todo)} unlabelled\n")
    for r in todo[:n]:
        path = os.path.join(TEXT_DIR, r["node_id"] + ".txt")
        text = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        body = text.split("\n\n", 1)[-1]
        print("=" * 100)
        print(f"{r['node_id']} | {r['date_published'][:10]} | {r['section']} | {r['author']}"
              f" | type: {r.get('ld_type', '')} | {r.get('word_count', '?')} words")
        print(r["title"])
        print(r["canonical_url"])
        print(f"tags: {', '.join(r['tags'][:12])}   hint-terms: {len(HINT.findall(body))}"
              f"   chars: {len(body)}")
        print("-" * 100)
        print(body[:6000])
        if len(body) > 6000:
            print(f"... [{len(body) - 6000} more chars in {path}]")


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "pending"
    if cmd == "pending":
        return pending(int(argv[2]) if len(argv) > 2 else 5)
    recs, labels = load_records(), load_labels()
    if cmd == "set":
        unsure = argv[argv.index("--unsure") + 1] if "--unsure" in argv else ""
        set_label(labels, recs, argv[2], argv[3], argv[4], argv[5], unsure)
    elif cmd == "import":
        with open(argv[2], newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                set_label(labels, recs, row["node_id"], row["label"], row["content_type"],
                          row["reason"], row.get("unsure_note", ""))
    save_labels(labels)
    print(f"{len(labels)} labelled")


if __name__ == "__main__":
    main(sys.argv)
