#!/usr/bin/env python3
"""List the relations that need a person's (or a reviewer's) judgement: every synonym, near
synonym or antonym whose word, or a word in it, is on one of the sensitive-word lists in
clean/sources/ (Wiktionary's slur, offensive, vulgar, swear and derogatory categories, and the
LDNOOBW list). Writes clean/review/flagged.tsv, one relation per line:

    id  headword  sense  pos  gloss  relation  word  register  lists

`id` is stable (headword|sense|relation|word), so decisions survive a rebuild.
"""
import gzip, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RELATIONS = ("synonyms", "near_synonyms", "antonyms")


def load_lists():
    lists = {}
    for f in sorted((ROOT / "sources").glob("*.txt")):
        for line in f.read_text(encoding="utf-8").splitlines():
            w = line.strip().lower()
            if w and not w.startswith("#"):
                lists.setdefault(w, set()).add(f.stem)
    return lists


def hits(word, lists):
    w = word.lower()
    found = set(lists.get(w, ()))
    for tok in re.findall(r"[a-z][a-z'\-]*", w):
        found |= lists.get(tok, set())
    return found


def relation_id(head, sense, relation, word):
    return f"{head}|{sense}|{relation}|{word}"


def main():
    lists = load_lists()
    rows = []
    src = ROOT.parent / "abcthesaurus-en.jsonl.gz"
    for o in map(json.loads, gzip.open(src, "rt", encoding="utf-8")):
        head_hits = hits(o["word"], lists)
        for i, s in enumerate(o["senses"]):
            for rel in RELATIONS:
                for x in s.get(rel, []):
                    h = hits(x["word"], lists)
                    # Antonyms of sensitive headwords are harmless ("whore" ↔ "virgin" is still flagged
                    # through the word itself); everything else with a hit on either side is reviewed.
                    if h or (head_hits and rel != "antonyms"):
                        rows.append([relation_id(o["word"], i, rel, x["word"]), o["word"], str(i), s["pos"],
                                     s["gloss"], rel, x["word"], x["register"], ",".join(sorted(h | head_hits))])
    out = ROOT / "review" / "flagged.tsv"
    out.write_text("\n".join("\t".join(r) for r in rows) + "\n", encoding="utf-8")
    print(f"{len(rows)} relations flagged -> {out}")


if __name__ == "__main__":
    main()
