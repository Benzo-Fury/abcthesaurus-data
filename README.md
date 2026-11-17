# Cilica thesaurus data

A cleaned English synonym graph for writing tools. It was made for [Cilica](https://github.com/Benzo-Fury/cilica), a private notes app, where a synonym is offered in one click without the writer seeing the sentence it came from. In that setting a wrong or offensive suggestion is worse than none.

**23,184 headwords, 32,878 senses, 340,992 relations.** Every synonym and antonym is attached to one meaning and labelled with its register (formal, slang and so on) and a relative intensity.

## Where this comes from

The data is the [ABC Thesaurus](https://abcthesaurus.com/). This repository is a fork of [warshipss/abcthesaurus-data](https://github.com/warshipss/abcthesaurus-data), which publishes that data. We did not collect or write the thesaurus. The original is the work of abcthesaurus.com and we are grateful for it.

We forked it because the raw data is good but was not safe to show to people unchecked. This repository adds one file, [`dist/abcthesaurus-en.clean.jsonl.gz`](dist/abcthesaurus-en.clean.jsonl.gz), and the pipeline and tests that produce it. The original files are still here, unchanged, so you can compare the two. [CHANGES.md](CHANGES.md) is the short version of this page.

## What we changed, and why

| Change | Why | How much |
| --- | --- | --- |
| **Slurs removed.** Ethnic, homophobic, ableist and similar slurs are never offered, in any meaning or relation. | A one-click replacement must never hand someone a slur. The raw data attached slur meanings to some ordinary words, so a plain word could offer a slur. | 18 words classed as slurs. Their relations are removed. |
| **Rude words marked** with `"rude": true`. A headword that is itself rude is marked too. | Swearing and crude words are fine when the writer chose a rude word and wrong when they did not. Offer a rude word only for a rude headword ("arse" gives "ass"), never for a plain one (a body part never offers its crude name). | 25 words classed as rude, 14 rude headwords, 326 relations marked. |
| **Out-of-context relations removed**, where an ordinary word pointed at a violent or sexual meaning it only shares in another sense. | A word list cannot see that a relation is right for one meaning of a word and wrong for another. These were decided one relation at a time. | 419 relations removed. |
| **Contradictions removed.** A word listed as both a synonym and an antonym of one meaning. | The data cannot be right both ways. | 5 removed. |
| **Everyday meanings added first**: "mum" (mother) and "gay" (attracted to the same sex). | The raw entries did not open with the meaning people mean most often. | 2 senses added. |

Together that is 0.12% of relations removed and 0.10% marked rude. Every headword is kept and the file has the same shape as the original, so it can replace it directly.

## How it is made

Nothing in the output is edited by hand. Every decision is a line in a file you can read, and `clean/build.py` applies them to the original data.

1. **Flag.** `clean/flag.py` lists every relation touching a word on Wiktionary's slur, offensive, vulgar, swear-word or derogatory lists, or on [LDNOOBW](https://github.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words). Those six lists in `clean/sources/` hold 15,304 entries between them (they overlap).
2. **Classify words.** Each of the 1,159 flagged words that appear in the thesaurus was classified once in `clean/review/words.tsv`:

   | Class | Words | Meaning |
   | --- | ---: | --- |
   | slur | 18 | Never offered. |
   | rude | 25 | Offered only for a rude headword. |
   | context | 119 | Depends on the meaning, so decided per relation. |
   | fine | 997 | The lists were over-cautious ("abc", "accident"). |

3. **Decide relations.** `clean/review/relations.tsv` holds 3,542 decisions, one relation each (3,094 keep, 313 remove, 135 rude). It covers every relation of a "context" word, every slang or dated use of a listed word, the errors the quality audit found, and a few hand decisions marked `manual` for words no list knows.
4. **Build.** `clean/build.py` applies the decisions, drops contradictions and adds the missing meanings from `clean/additions.json`. It writes `dist/abcthesaurus-en.clean.jsonl.gz` and the counts in `dist/report.json`.

```bash
python3 clean/flag.py          # list relations to review
python3 clean/build.py         # write dist/
python3 clean/readme.py        # run the tests and refresh the results below (fails if any test fails)
```

## Benchmarks

There are two kinds of check: a test suite that guards the cleaned file, and a quality audit that measures how good the original suggestions were. The tables further down are rewritten by `clean/readme.py` each time the tests run.

### Tests

`clean/tests/test_clean.py` loads the result once and fails if any of these slip:

- **Slurs.** None is ever offered, including a canary check against hashed versions of the worst English slurs that does not depend on our review files. The slur meanings of ordinary words are gone.
- **Rude words.** Every rude word is marked. Plain words never offer them (an everyday word never gets its crude or demeaning slang). Rude headwords still get their rude synonyms.
- **Out of context.** Known bad relations stay gone (ordinary words never offer violent or sexual out-of-context meanings). Innocent meanings survive ("accompany" to escort, "grab" to snatch).
- **Contradictions.** Nothing is both a synonym and an antonym of one meaning, and no word is its own synonym.
- **Meanings.** Everyday meanings come first, and common words get good answers.
- **Integrity.** Every headword is kept and the clean-up removes less than 1% of relations. Every flagged word was reviewed and every decision is applied. Strings are plain text and every record carries the licence and credit.
- **Speed.** The whole suite runs in a few seconds.

### Quality audit

We judged a random sample of 900 suggestions, taken from words with three or more meanings, as "ok" or "wrong" in context (`clean/review/audit.tsv`). The wrong ones were removed.

The result shaped how Cilica uses the data. Close synonyms were wrong 1.3% of the time and near synonyms 28.0%, because near synonyms often come from a different meaning of either word. A tool that replaces a word in one click should offer `synonyms` only, or show `near_synonyms` apart as looser ideas.

### Latest results

<!-- clean:start -->
**20 of 20 checks pass** (2.7 s, run 2026-11-16).

| Group | Check | Result |
| --- | --- | --- |
| Contradictions | No word is its own synonym | ✅ |
| Contradictions | Nothing is both alike and opposite | ✅ |
| Integrity | Clean up removes little | ✅ |
| Integrity | Every flagged word was reviewed | ✅ |
| Integrity | Every headword kept and shape unchanged | ✅ |
| Integrity | Every relation decision is applied | ✅ |
| Integrity | License and attribution | ✅ |
| Integrity | Strings are plain text | ✅ |
| Meanings | Everyday meanings come first | ✅ |
| Meanings | Good answers for common words | ✅ |
| OutOfContext | Innocent meanings survive | ✅ |
| OutOfContext | Violent and sexual words stay in their meaning | ✅ |
| RudeWords | Every rude word is marked | ✅ |
| RudeWords | No plain headword is marked rude | ✅ |
| RudeWords | Plain words never offer rude ones | ✅ |
| RudeWords | Rude words offer their rude synonyms | ✅ |
| Slurs | Canary slurs never appear | ✅ |
| Slurs | No slur is ever offered | ✅ |
| Slurs | Slur meanings of ordinary words are gone | ✅ |
| Speed | Loads quickly | ✅ |

Quality audit: a random sample of suggestions for words with three or more meanings, each judged by a reviewer (`clean/review/audit.tsv`). The wrong ones are removed from the cleaned data.

| Relation | Judged | Wrong | Wrong rate |
| --- | ---: | ---: | ---: |
| synonyms | 457 | 6 | 1.3% |
| near_synonyms | 443 | 124 | 28.0% |

What the clean-up changed (`dist/report.json`):

| | Count |
| --- | ---: |
| headwords | 23,184 |
| rude headwords | 14 |
| antonyms:keep | 66,110 |
| antonyms:remove | 21 |
| antonyms:rude | 104 |
| contradictions removed | 5 |
| near_synonyms:keep | 101,085 |
| near_synonyms:remove | 276 |
| near_synonyms:rude | 102 |
| senses added | 2 |
| synonyms:keep | 173,052 |
| synonyms:remove | 122 |
| synonyms:rude | 120 |
<!-- clean:end -->

### What these numbers do not tell you

- The audit sample is 900 suggestions judged by one reviewer, not an independent panel. Treat 1.3% and 28.0% as estimates.
- It covers words with three or more meanings, where mix-ups are most likely. Words with one or two meanings were not sampled.
- The sample is what we fixed, so the error rate after the clean-up has not been measured. We know the 130 errors it found are gone, not that no others remain.
- The slur and rude checks are only as good as the word lists and our review. A word on no list, used in a way we did not think of, can still get through. Tell us if you find one.

## Using it

Each record has the same shape as the original, plus `"rude": true` on rude relations and on headwords that are themselves rude.

```json
{"word": "sterling",
 "senses": [{"pos": "adj", "gloss": "of the finest quality",
   "synonyms": [{"word": "excellent",   "register": "neutral",  "intensity": 0},
                {"word": "first rate",  "register": "informal", "intensity": 0},
                {"word": "meritorious", "register": "formal",   "intensity": 0}],
   "near_synonyms": [{"word": "exquisite", "register": "formal", "intensity": 1}],
   "antonyms": [{"word": "second-rate", "register": "neutral", "intensity": 0}]}],
 "examples": ["Tom is doing sterling work."],
 "license": "CC BY-SA 4.0. Data from ABC Thesaurus (https://abcthesaurus.com), cleaned in https://github.com/Benzo-Fury/abcthesaurus-data (see CHANGES.md)"}
```

| Field | Values |
| --- | --- |
| `pos` | noun, verb, adj, adv, prep, pron, conj, other |
| `register` | neutral, formal, informal, slang, dated, literary, technical |
| `intensity` | integer from -2 to +2, relative to the headword (good to superb is +1) |
| `rude` | `true` on a rude relation or a rude headword, otherwise absent |

Offer a rude word only for a rude headword:

```python
import gzip, json

with gzip.open("dist/abcthesaurus-en.clean.jsonl.gz", "rt", encoding="utf-8") as f:
    thesaurus = {o["word"]: o for o in map(json.loads, f)}

def synonyms(word):
    entry = thesaurus[word]
    rude_ok = entry.get("rude", False)
    for sense in entry["senses"]:
        yield sense["gloss"], [s["word"] for s in sense["synonyms"] if rude_ok or not s.get("rude")]

for gloss, words in synonyms("breast"):
    print(gloss, "->", words)
```

### In Cilica

Cilica's [`cilica-thesaurus`](https://github.com/Benzo-Fury/cilica/tree/main/crates/thesaurus) crate builds its bundled file from this one with `tools/build-thesaurus.py`. It keeps close synonyms only, drops near synonyms and antonyms, and keeps rude words only for rude headwords. That takes the bundle to about 1.2 MB, read in about 0.2 s in a debug build, with no network use.

## Files

| File | Contents |
| --- | --- |
| [`dist/abcthesaurus-en.clean.jsonl.gz`](dist/abcthesaurus-en.clean.jsonl.gz) | The cleaned graph, one JSON object per headword (3.0 MB). Use this. |
| [`dist/report.json`](dist/report.json) | Counts of everything the clean-up changed. |
| [`clean/`](clean) | The pipeline, the word lists, our review decisions and the tests. |
| `abcthesaurus-en.jsonl.gz` | The original graph, unchanged (3.0 MB). |
| `abcthesaurus-en-edges.csv.gz` | The original as a flat table of all 340,992 relations. Not cleaned. |
| `abcthesaurus-vs-notes.csv.gz` | About 4.5k editorial "what's the difference" notes for confusable pairs, from the original. Not cleaned. |

The original data and its JSON API are published at [abcthesaurus.com/data](https://abcthesaurus.com/data/). For the unmodified data, get it from there.

## Licence and credit

- **Data:** [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). The cleaned file is an adaptation of the ABC Thesaurus, so it is shared under the same licence. If you share it or something built from it, keep the credit, link the licence, say it was changed, and use the same licence. Use this line:

  > Thesaurus data © [ABC Thesaurus](https://abcthesaurus.com/), CC BY-SA 4.0, cleaned in [github.com/Benzo-Fury/abcthesaurus-data](https://github.com/Benzo-Fury/abcthesaurus-data).

- **Examples** inside the data come from [Tatoeba](https://tatoeba.org) (CC BY 2.0 FR).
- **Word lists** in `clean/sources/` are Wiktionary category listings (CC BY-SA 4.0) and LDNOOBW (CC BY 4.0).
- **Code** in `clean/`: MIT.

This project is not endorsed by abcthesaurus.com.
