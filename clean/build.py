#!/usr/bin/env python3
"""Build dist/abcthesaurus-en.clean.jsonl.gz: the ABC Thesaurus with slurs taken out, rude words marked,
wrong relations removed and a few missing meanings added. Nothing is edited by hand in the output; every
change comes from one of these reviewed files:

    clean/review/words.tsv       word  class  note       how a sensitive word is treated everywhere
    clean/review/relations.tsv   id    action note       a decision for one relation (overrides words.tsv)
    clean/additions.json         meanings to add to a headword, placed first

Word classes:
    slur     never offered (ethnic, homophobic, ableist and similar slurs, in every sense)
    rude     offered only for a headword that is itself rude: swearing, crude sexual or bodily words
    context  harmless in some meanings and not in others: decided per relation in relations.tsv,
             and treated as rude where no decision exists
    fine     the source lists were over-cautious; offered as usual

Relation actions: keep, rude, remove. A relation's id is `headword|sense|relation|word`
(sense is the 0-based index in the upstream data).

Also automatic: a word listed as both a synonym and an antonym of one meaning is dropped from both.

Output: one JSON object per headword, the upstream shape plus `"rude": true` on rude relations and on
headwords that are themselves rude, and a `license` field. A summary goes to dist/report.json.
"""

import gzip
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UPSTREAM = ROOT.parent / "abcthesaurus-en.jsonl.gz"
DIST = ROOT.parent / "dist"
RELATIONS = ("synonyms", "near_synonyms", "antonyms")
CLASSES = {"slur", "rude", "context", "fine"}
ACTIONS = {"keep", "rude", "remove"}
LICENSE = ("CC BY-SA 4.0. Data from ABC Thesaurus (https://abcthesaurus.com), cleaned in "
           "https://github.com/Benzo-Fury/abcthesaurus-data (see CHANGES.md)")


def tokens(text: str) -> list[str]:
    """The whole text and each word in it, lower case: "pompous ass" → [pompous ass, pompous, ass]."""
    t = text.lower()
    return [t, *re.findall(r"[a-z][a-z'\-]*", t)]


def relation_id(head: str, sense: int, relation: str, word: str) -> str:
    return f"{head}|{sense}|{relation}|{word}"


def read_tsv(path: Path, width: int) -> list[list[str]]:
    rows = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.split("\t")
        if len(f) < width:
            raise SystemExit(f"{path.name}:{n}: expected {width} tab-separated fields")
        rows.append(f)
    return rows


def load_reviews():
    words = {}
    for w, cls, *_ in read_tsv(ROOT / "review" / "words.tsv", 2):
        if cls not in CLASSES:
            raise SystemExit(f"words.tsv: unknown class {cls!r} for {w!r}")
        words[w.lower()] = cls
    decisions = {}
    for rid, action, *_ in read_tsv(ROOT / "review" / "relations.tsv", 2):
        if action not in ACTIONS:
            raise SystemExit(f"relations.tsv: unknown action {action!r} for {rid!r}")
        decisions[rid] = action
    additions = json.loads((ROOT / "additions.json").read_text(encoding="utf-8"))
    return words, decisions, additions


def word_class(text: str, words: dict[str, str]) -> str:
    """The strictest class of the text or any word in it."""
    found = {words.get(t) for t in tokens(text)} - {None}
    for cls in ("slur", "rude", "context"):
        if cls in found:
            return cls
    return "fine"


def build():
    words, decisions, additions = load_reviews()
    stats = Counter()
    used_decisions = set()
    out = []
    for o in map(json.loads, gzip.open(UPSTREAM, "rt", encoding="utf-8")):
        head = o["word"]
        senses = []
        for i, s in enumerate(o["senses"]):
            s = dict(s)
            for rel in RELATIONS:
                kept = []
                for x in s.get(rel, []):
                    rid = relation_id(head, i, rel, x["word"])
                    cls = word_class(x["word"], words)
                    action = decisions.get(rid)
                    if action:
                        used_decisions.add(rid)
                    elif cls == "slur":
                        action = "remove"
                    elif cls in ("rude", "context"):
                        action = "rude"
                    else:
                        action = "keep"
                    stats[f"{rel}:{action}"] += 1
                    if action == "remove":
                        continue
                    x = dict(x)
                    if action == "rude":
                        x["rude"] = True
                    kept.append(x)
                s[rel] = kept
            # A word cannot be both like and unlike one meaning.
            alike = {x["word"].lower() for r in RELATIONS[:2] for x in s[r]}
            both = alike & {x["word"].lower() for x in s["antonyms"]}
            if both:
                stats["contradictions removed"] += len(both)
                for r in RELATIONS:
                    s[r] = [x for x in s[r] if x["word"].lower() not in both]
            senses.append(s)
        for add in additions.get(head, []):
            stats["senses added"] += 1
            senses.insert(0, add)
        record = {"word": head, **({"rude": True} if word_class(head, words) == "rude" else {}),
                  **{k: v for k, v in o.items() if k not in ("word", "senses", "license")},
                  "senses": senses, "license": LICENSE}
        out.append(record)
    missing = set(additions) - {o["word"] for o in out}
    if missing:
        raise SystemExit(f"additions.json: no such headwords: {sorted(missing)}")
    stale = set(decisions) - used_decisions
    if stale:
        raise SystemExit(f"relations.tsv: {len(stale)} decisions match no relation, e.g. {sorted(stale)[:3]}")

    DIST.mkdir(exist_ok=True)
    with gzip.GzipFile(DIST / "abcthesaurus-en.clean.jsonl.gz", "wb", compresslevel=9, mtime=0) as f:
        for o in out:
            f.write((json.dumps(o, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"))
    report = {"headwords": len(out), "rude headwords": sum(1 for o in out if o.get("rude")), **dict(sorted(stats.items()))}
    (DIST / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    build()
