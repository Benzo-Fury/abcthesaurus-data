# Changes in this fork

This fork of [warshipss/abcthesaurus-data](https://github.com/warshipss/abcthesaurus-data) keeps the
upstream files unchanged and adds a cleaned copy, `dist/abcthesaurus-en.clean.jsonl.gz`, for use in
writing tools where a synonym is offered without seeing the sentence. Like the original, the cleaned
data is licensed [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Credit:
"Thesaurus data © [ABC Thesaurus](https://abcthesaurus.com/), CC BY-SA 4.0, cleaned in
github.com/Benzo-Fury/abcthesaurus-data".

## What changed

- **Slurs are removed.** Ethnic, homophobic, ableist and similar slurs are never offered as a synonym,
  near synonym or antonym, in any meaning, including slur meanings that were attached to ordinary words.
- **Rude words are marked.** Swearing and crude sexual or bodily words carry `"rude": true`, and a
  headword that is itself rude carries `"rude": true` too. Tools should offer a rude word only for a
  rude headword ("arse" → ass), never for a plain one.
- **Out-of-context relations are removed**, where an ordinary word pointed at a violent or sexual
  meaning it only shares in another sense.
- **Contradictions are removed**: a word listed as both a synonym and an antonym of one meaning.
- **Missing everyday meanings are added first**: "mum" (mother), "gay" (attracted to the same sex).

`dist/report.json` counts every change.

## How

Nothing in the output is edited by hand. `clean/flag.py` lists every relation that touches a word on
Wiktionary's slur, offensive, vulgar, swear-word and derogatory categories or the LDNOOBW list
(`clean/sources/`). Each flagged word was classified once (`clean/review/words.tsv`: slur, rude,
context or fine), and words that are harmless in some meanings were decided relation by relation
(`clean/review/relations.tsv`), as were slang and dated uses of listed words. A random sample of 900 suggestions was audited for out-of-context answers (`clean/review/audit.tsv`); the wrong ones are removed too, and a handful of decisions for words no list knows are marked `manual`. `clean/build.py` applies those decisions to the upstream file.

```bash
python3 clean/flag.py                                  # list relations to review
python3 clean/build.py                                 # write dist/
python3 -m unittest discover -s clean/tests -v         # check the result
```

The tests fail if a slur or rude word slips through, if a known out-of-context relation comes back,
if a flagged word has no decision, or if the clean-up removes more than 1% of relations.

Word lists in `clean/sources/`: Wiktionary category listings (CC BY-SA 4.0) and
[LDNOOBW](https://github.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words) (CC BY 4.0).
