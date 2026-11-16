"""Checks on dist/abcthesaurus-en.clean.jsonl.gz, written to catch the problems the clean-up exists for:
slurs offered as synonyms, rude words offered for plain words, out-of-context relations, contradictions,
and missing everyday meanings. Also guards the review itself: every flagged word must have a decision,
and the clean-up must not quietly delete much of the thesaurus.

    python3 -m unittest discover -s clean/tests -v

The output is loaded once; every check is a pass over in-memory sets, so the suite runs in seconds.
"""

import gzip
import hashlib
import json
import re
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "clean"))
import build  # noqa: E402
import flag  # noqa: E402

RELATIONS = ("synonyms", "near_synonyms", "antonyms")
START = time.perf_counter()
UPSTREAM = {o["word"]: o for o in map(json.loads, gzip.open(ROOT / "abcthesaurus-en.jsonl.gz", "rt", encoding="utf-8"))}
CLEAN = {o["word"]: o for o in map(json.loads, gzip.open(ROOT / "dist" / "abcthesaurus-en.clean.jsonl.gz", "rt", encoding="utf-8"))}
WORDS, DECISIONS, ADDITIONS = build.load_reviews()
LOADED = time.perf_counter() - START

# The worst English slurs, as SHA-256 of the lower-case word so they need not be spelled out here. A
# canary independent of the review files: if one of these is ever offered, the review missed it.
CANARIES = {
    "120f6e5b4ea32f65bda68452fcfaaef06b0136e1d0e4a6f60bc3771fa0936dd6",
    "08a841e996781e9e77d30a4e4420a8f501a280b00624e6d1224bf54aaff73eba",
    "c3de533e9b7fe63b79f648687a30d2861edd92fe7c3cd1f2c485e0a605367624",
    "98b52c4b6b7d1f48e7477a5ccc10955dd195d0ac5a38c8281bfeb08762634909",
    "eef3bd091670c3447022d619c06ad15de96da72b5a66f28bb8b75d1b1c12a05f",
    "f9d0d9b18ae9033a5ea36df19bf279b059e887a9ae785db81117bceaecc95933",
    "cc02032349c833ac5e97bac094560ed40e09acf34cb1978ab7a9840b9bf15b4d",
    "8f5083e3e5c7dc8932f2bf58212f963f3a44752618c96297f82623f736c52738",
    "9915ba2d822280f22c283df4e76584a40e0119fc58f73c5f84d4fdb04d04fa6f",
    "16ea09fc78ca83ca502cbcf2377acdf280bf18f61e259153f0868405eedab5ef",
    "e7b98c6aa5b944e0b315d350d423f895ac9e44fb84f1534b18c2572370a67b9e",
    "22fc75e65a0e9d34324092a7c6a8dba961853294abca4e5914e60c550f48e0c2",
    "333f7618092958c75b8c5af6f1ec77b42803922a0fc6ff1570a8af3a3aab3b4a",
    "3b1e0d7c5dd45583867e897943e37a940a7e7321022317dd3deea01963ee365e",
    "158869a97379229b7681efae9d7f9c9214134e836d649ba53477c0c111414d59",
    "886d51e97ad7931d0d2af8439ca6d9e4887e3c2b469ed247cbd68ceb3649ccde",
    "12e6274e4309293e2d480272b49a6c7c73a6a6b22678ba226b533c67006c17d1",
    "469c0fdb6020d4bffe12ec93e76150a08ef02e116fc856a84b24eb02a1d1a155",
    "6d1833779e389477ac6757e19c371df8e141bd67bc83e4b596dfc8a1947db29d",
    "0f9326dff651fe0347281f245745fc879090339e7029dc1e44ca7bf12cf2832d",
}


def offered(word: str) -> list[str]:
    """What an app shows for `word`: synonyms and near synonyms, rude ones only for a rude headword."""
    o = CLEAN[word]
    return [x["word"] for s in o["senses"] for r in RELATIONS[:2] for x in s.get(r, [])
            if o.get("rude") or not x.get("rude")]


def all_relations(data):
    for o in data.values():
        for i, s in enumerate(o["senses"]):
            for r in RELATIONS:
                for x in s.get(r, []):
                    yield o, i, s, r, x


class Slurs(unittest.TestCase):
    def test_no_slur_is_ever_offered(self):
        slurs = {w for w, c in WORDS.items() if c == "slur"}
        bad = [(o["word"], x["word"]) for o, _, _, _, x in all_relations(CLEAN)
               if slurs & set(build.tokens(x["word"]))]
        self.assertEqual(bad, [], "slurs left in relations")

    def test_canary_slurs_never_appear(self):
        seen = {hashlib.sha256(t.encode()).hexdigest() for o, *_, x in all_relations(CLEAN) for t in build.tokens(x["word"])}
        self.assertFalse(seen & CANARIES)

    def test_slur_meanings_of_ordinary_words_are_gone(self):
        # Ordinary words that are also slurs: the slur is never offered, the ordinary word still is.
        self.assertNotIn("chink", [w.lower() for w in offered("crack")])
        self.assertNotIn("gyp", [w.lower() for w in offered("cheat")])
        self.assertNotIn("retard", [w.lower() for w in offered("crimp")])
        self.assertNotIn("colored", [w.lower() for w in offered("black")])
        self.assertNotIn("half-breed", [w.lower() for w in offered("half blood")])
        for word in ("tire", "fatigue", "weary", "wear out"):
            self.assertNotIn("fag", offered(word), word)
        self.assertIn("gap", offered("chink"))


class RudeWords(unittest.TestCase):
    def test_every_rude_word_is_marked(self):
        rude = {w for w, c in WORDS.items() if c == "rude"}
        unmarked = [(o["word"], x["word"]) for o, i, s, r, x in all_relations(CLEAN)
                    if rude & set(build.tokens(x["word"])) and not x.get("rude")
                    and DECISIONS.get(build.relation_id(o["word"], i, r, x["word"])) != "keep"]
        self.assertEqual(unmarked, [])

    def test_plain_words_never_offer_rude_ones(self):
        cases = {
            "breast": "tit", "detective": "dick", "complain": "bitch", "drink": "hooker",
            "prostitute": "whore", "woman": "broad",
            "lustful": "horny", "jezebel": "bitch", "teat": "tit", "purulent": "pussy",
            "blunder": "boner", "sleuth": "dick", "termagant": "bitch",
        }
        for plain, rude in cases.items():
            self.assertNotIn(rude, offered(plain), plain)

    def test_rude_words_offer_their_rude_synonyms(self):
        self.assertTrue(CLEAN["arse"].get("rude"))
        self.assertIn("ass", offered("arse"))
        self.assertIn("butt", offered("arse"))

    def test_no_plain_headword_is_marked_rude(self):
        for word in ("customer", "happy", "breast", "drink", "woman", "tire", "rooster"):
            self.assertFalse(CLEAN[word].get("rude"), word)


class OutOfContext(unittest.TestCase):
    def test_violent_and_sexual_words_stay_in_their_meaning(self):
        self.assertNotIn("rape", offered("aggression"))
        self.assertNotIn("rape", offered("assault"))
        self.assertNotIn("bestiality", offered("brutality"))
        self.assertNotIn("bestiality", offered("inhumanity"))
        self.assertNotIn("threesome", offered("trilogy"))
        self.assertNotIn("threesome", offered("triangle"))
        self.assertNotIn("fingering", offered("rub"))
        self.assertNotIn("spastic", offered("choppy"))
        self.assertNotIn("ejaculation", offered("cry"))

    def test_innocent_meanings_survive(self):
        self.assertIn("escort", offered("accompany"))
        self.assertIn("snatch", offered("grab"))
        self.assertIn("orgy", offered("binge") + offered("bacchanal"))


class Contradictions(unittest.TestCase):
    def test_nothing_is_both_alike_and_opposite(self):
        for o in CLEAN.values():
            for s in o["senses"]:
                alike = {x["word"].lower() for r in RELATIONS[:2] for x in s.get(r, [])}
                unlike = {x["word"].lower() for x in s.get("antonyms", [])}
                self.assertFalse(alike & unlike, (o["word"], s["gloss"]))

    def test_no_word_is_its_own_synonym(self):
        for o, _, _, r, x in all_relations(CLEAN):
            if r != "antonyms":
                self.assertNotEqual(o["word"].lower(), x["word"].lower())


class Meanings(unittest.TestCase):
    def test_everyday_meanings_come_first(self):
        self.assertEqual(CLEAN["mum"]["senses"][0]["pos"], "noun")
        self.assertIn("mother", offered("mum")[:3])
        self.assertIn("homosexual", offered("gay")[:3])

    def test_good_answers_for_common_words(self):
        expect = {
            "customer": {"client", "buyer", "consumer", "shopper"},
            "happy": {"glad", "cheerful"},
            "big": {"large", "enormous"},
            "idea": {"thought", "concept"},
            "problem": {"dilemma", "puzzle"},
            "interview": {"meeting", "conversation"},
        }
        for word, wanted in expect.items():
            self.assertTrue(wanted <= set(offered(word)), (word, offered(word)))


class Integrity(unittest.TestCase):
    def test_every_headword_kept_and_shape_unchanged(self):
        self.assertEqual(set(CLEAN), set(UPSTREAM))
        keys = {"word", "senses", "license", "examples", "url", "examples_license", "rude"}
        for o in CLEAN.values():
            self.assertLessEqual(set(o), keys)
            for s in o["senses"]:
                self.assertTrue(s["gloss"] and s["pos"])

    def test_clean_up_removes_little(self):
        before = sum(1 for _ in all_relations(UPSTREAM))
        after = sum(1 for _ in all_relations(CLEAN))
        self.assertGreater(after / before, 0.99, (before, after))

    def test_every_flagged_word_was_reviewed(self):
        lists = flag.load_lists()
        unreviewed = set()
        for o, *_, x in all_relations(UPSTREAM):
            for t in build.tokens(x["word"]):
                if t in lists and t not in WORDS:
                    unreviewed.add(t)
        self.assertEqual(sorted(unreviewed), [])

    def test_every_relation_decision_is_applied(self):
        present = {}
        for o, i, s, r, x in all_relations(CLEAN):
            present[build.relation_id(o["word"], i - len(ADDITIONS.get(o["word"], [])), r, x["word"])] = x
        # Words listed as both like and unlike one meaning are dropped whatever the decision.
        contradicted = set()
        for o in UPSTREAM.values():
            for i, s in enumerate(o["senses"]):
                unlike = {x["word"].lower() for x in s.get("antonyms", [])}
                for r in RELATIONS[:2]:
                    contradicted |= {build.relation_id(o["word"], i, r, x["word"]) for x in s.get(r, []) if x["word"].lower() in unlike}
        for rid, action in DECISIONS.items():
            if rid in contradicted:
                self.assertFalse(rid in present, rid)
            elif action == "remove":
                self.assertFalse(rid in present, rid)
            else:
                self.assertTrue(rid in present, rid)
                self.assertEqual(bool(present[rid].get("rude")), action == "rude", rid)

    def test_strings_are_plain_text(self):
        ok = re.compile(r"^[\w '\-\.,/&()!?’]+$")
        for o, *_, x in all_relations(CLEAN):
            self.assertRegex(x["word"], ok)
            self.assertLess(len(x["word"]), 48)

    def test_license_and_attribution(self):
        for o in CLEAN.values():
            self.assertIn("CC BY-SA 4.0", o["license"])
            self.assertIn("abcthesaurus.com", o["license"])


class Speed(unittest.TestCase):
    def test_loads_quickly(self):
        self.assertLess(LOADED, 10, f"loading took {LOADED:.1f}s")


if __name__ == "__main__":
    unittest.main()
