# ABC Thesaurus — open English synonym graph

> **This fork adds a cleaned copy for writing tools:** [`dist/abcthesaurus-en.clean.jsonl.gz`](dist/abcthesaurus-en.clean.jsonl.gz),
> with slurs removed, rude words marked, out-of-context relations removed and a test suite that checks it.
> The upstream files below are unchanged. See [Cleaned data](#cleaned-data-this-fork) and [CHANGES.md](CHANGES.md).

Sense-level English thesaurus data: **23,184 headwords, 32,878 senses, 340,992 verified relations** — every synonym/antonym attached to a specific meaning and labeled with **register** and **relative intensity**.

Maintained by [abcthesaurus.com](https://abcthesaurus.com/); this repo hosts documentation and loading examples. Data downloads live at **https://abcthesaurus.com/data/**.

## What's in the data

| Field | Values |
|---|---|
| `pos` | noun, verb, adj, adv, prep, pron, conj, other |
| `register` | neutral, formal, informal, slang, dated, literary, technical |
| `intensity` | integer −2…+2, relative to the headword (good → superb = +1) |
| relations | `synonyms`, `near_synonyms`, `antonyms` — all sense-level |

Example record (JSONL, one object per headword):

```json
{"word": "sterling",
 "senses": [{"pos": "adj", "gloss": "of the finest quality",
   "synonyms": [{"word": "excellent",   "register": "neutral",  "intensity": 0},
                {"word": "first rate",  "register": "informal", "intensity": 0},
                {"word": "meritorious", "register": "formal",   "intensity": 0}],
   "near_synonyms": [{"word": "exquisite", "register": "formal", "intensity": 1}],
   "antonyms": [{"word": "second-rate", "register": "neutral", "intensity": 0}]}],
 "examples": ["Tom is doing sterling work."]}
```

## Files

| File | Contents |
|---|---|
| [`abcthesaurus-en.jsonl.gz`](https://abcthesaurus.com/data/abcthesaurus-en.jsonl.gz) | Full graph, one JSON object per headword (2.9 MB) |
| [`abcthesaurus-en-edges.csv.gz`](https://abcthesaurus.com/data/abcthesaurus-en-edges.csv.gz) | Flat table of all 340,992 relations (2.8 MB) |
| [`abcthesaurus-vs-notes.csv.gz`](https://abcthesaurus.com/data/abcthesaurus-vs-notes.csv.gz) | ~4.5k editorial "what's the difference" notes for confusable pairs |

## JSON API

Every word is also served as JSON, no key required:

```
GET https://abcthesaurus.com/api/<word-slug>.json
```

Try it: [`/api/sterling.json`](https://abcthesaurus.com/api/sterling.json). For bulk work please use the dump, not the API.

## Quick start

```python
import gzip, json, urllib.request

url = "https://abcthesaurus.com/data/abcthesaurus-en.jsonl.gz"
urllib.request.urlretrieve(url, "thesaurus.jsonl.gz")

with gzip.open("thesaurus.jsonl.gz", "rt", encoding="utf-8") as f:
    thesaurus = {o["word"]: o for o in map(json.loads, f)}

# all informal synonyms of "drink" (verb senses)
for sense in thesaurus["drink"]["senses"]:
    if sense["pos"] == "verb":
        print(sense["gloss"], "->",
              [s["word"] for s in sense["synonyms"] if s["register"] == "informal"])
```

Pandas, straight from the flat CSV:

```python
import pandas as pd
df = pd.read_csv("https://abcthesaurus.com/data/abcthesaurus-en-edges.csv.gz")
df[(df.relation == "synonym") & (df.register == "slang")].head()
```

## Use cases

- **Formality rewriting / style transfer** — pick a synonym by `register`
- **Paraphrase strength control** — walk edges by `intensity`
- **WSD evaluation** — antonyms are disambiguated per sense
- **Writing tools** — suggestions that won't propose *quaff* in a business email

## License

Data: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) — attribution with a link to [abcthesaurus.com](https://abcthesaurus.com/) required.
Usage examples inside the data are from [Tatoeba](https://tatoeba.org) (CC BY 2.0 FR).
Code in this repo: MIT.

A line like *"Thesaurus data © [ABC Thesaurus](https://abcthesaurus.com/), CC BY-SA 4.0"* is perfect.

## Cleaned data (this fork)

`dist/abcthesaurus-en.clean.jsonl.gz` has the same shape as `abcthesaurus-en.jsonl.gz`, plus `"rude": true` on rude relations and on headwords that are themselves rude. Offer a rude word only for a rude headword. [CHANGES.md](CHANGES.md) says what was changed and why.

### How it's made

Nothing in the output is edited by hand:

1. **Flag.** `clean/flag.py` lists every relation touching a word on Wiktionary's slur, offensive, vulgar, swear-word or derogatory categories, or the LDNOOBW list (`clean/sources/`).
2. **Classify words.** Each of the 1,159 flagged words was classified once in `clean/review/words.tsv`:
   - **slur:** never offered
   - **rude:** only for rude headwords
   - **context:** depends on meaning, so decided per relation
   - **fine:** the lists were over-cautious
3. **Decide relations.** `clean/review/relations.tsv` decides one relation at a time (keep, rude or remove). It covers every relation of a "context" word, every slang or dated use of a listed word, the errors the quality audit found, and a few hand decisions marked `manual`.
4. **Build.** `clean/build.py` applies those decisions to the upstream file. It also drops any word listed as both a synonym and an antonym of one meaning, and adds the missing everyday meanings in `clean/additions.json`.

### Tests

`clean/tests/test_clean.py` loads the result once and checks:

- **Slurs:** no slur is ever offered, including a canary check against hashed versions of the worst English slurs that doesn't depend on the review files. The slur meanings of ordinary words are gone ("crack" never offers "chink").
- **Rude words:**
  - Every rude word is marked.
  - Plain words never offer rude ones ("breast" never gives "tit", "detective" never gives "dick", "woman" never gives "broad").
  - Rude headwords still get their rude synonyms ("arse" gives "ass").
- **Out of context:**
  - Known bad relations stay gone ("aggression" → rape, "trilogy" → threesome, "rub" → fingering).
  - Innocent meanings survive ("accompany" → escort, "grab" → snatch).
- **Contradictions:** nothing is both a synonym and an antonym of one meaning, and no word is its own synonym.
- **Meanings:** everyday meanings come first ("mum" → mother, "gay" → homosexual), and common words get good answers.
- **Integrity:**
  - Every headword is kept, and the clean-up removes less than 1% of relations.
  - Every flagged word was reviewed, and every decision is applied.
  - Strings are plain text, and every record carries the licence and attribution.
- **Speed:** the whole suite runs in seconds.

```bash
python3 clean/flag.py          # list relations to review
python3 clean/build.py         # write dist/
python3 clean/readme.py        # run the tests and refresh the results below (fails if any test fails)
```

### Latest results

<!-- clean:start -->
**20 of 20 checks pass** (1.2 s, run 2026-11-16).

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

### Using the near synonyms

The audit above finds that `near_synonyms` are wrong far more often than `synonyms`: they often come from a different meaning of either word. A tool that replaces words in one click should offer `synonyms` only, or show near synonyms apart as looser ideas.
