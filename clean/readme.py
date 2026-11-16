#!/usr/bin/env python3
"""Run the test suite and write its results, with the build's counts, into README.md between the
`<!-- clean:start -->` and `<!-- clean:end -->` markers. Exits non-zero if a test fails, so a stale or
failing README is never committed by accident.

    python3 clean/readme.py
"""

import io
import json
import sys
import time
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
README = ROOT.parent / "README.md"
START, END = "<!-- clean:start -->", "<!-- clean:end -->"


def run_tests():
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    results = []

    class Recorder(unittest.TextTestResult):
        def addSuccess(self, test):
            super().addSuccess(test)
            results.append((test, "pass"))

        def addFailure(self, test, err):
            super().addFailure(test, err)
            results.append((test, "FAIL"))

        def addError(self, test, err):
            super().addError(test, err)
            results.append((test, "ERROR"))

    start = time.perf_counter()
    outcome = unittest.TextTestRunner(stream=io.StringIO(), resultclass=Recorder).run(suite)
    return results, time.perf_counter() - start, outcome


def audit_rows() -> list[str]:
    rows = [l.split("\t") for l in (ROOT / "review" / "audit.tsv").read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#")]
    out = []
    for rel in ("synonyms", "near_synonyms"):
        rs = [r for r in rows if r[0].split("|")[2] == rel]
        wrong = sum(r[1] == "wrong" for r in rs)
        out.append(f"| {rel} | {len(rs)} | {wrong} | {wrong / len(rs):.1%} |")
    return out


def doc(test) -> str:
    name = test._testMethodName.removeprefix("test_").replace("_", " ")
    return name[0].upper() + name[1:]


def main():
    results, seconds, outcome = run_tests()
    report = json.loads((ROOT.parent / "dist" / "report.json").read_text())
    passed = sum(1 for _, r in results if r == "pass")
    lines = [
        START,
        f"**{passed} of {len(results)} checks pass** ({seconds:.1f} s, run {date.today().isoformat()}).",
        "",
        "| Group | Check | Result |",
        "| --- | --- | --- |",
        *[f"| {t.__class__.__name__} | {doc(t)} | {'✅' if r == 'pass' else '❌ ' + r} |" for t, r in results],
        "",
        "Quality audit: a random sample of suggestions for words with three or more meanings, each judged "
        "by a reviewer (`clean/review/audit.tsv`). The wrong ones are removed from the cleaned data.",
        "",
        "| Relation | Judged | Wrong | Wrong rate |",
        "| --- | ---: | ---: | ---: |",
        *audit_rows(),
        "",
        "What the clean-up changed (`dist/report.json`):",
        "",
        "| | Count |",
        "| --- | ---: |",
        *[f"| {k} | {v:,} |" for k, v in report.items()],
        END,
    ]
    text = README.read_text(encoding="utf-8")
    if START in text:
        before, rest = text.split(START, 1)
        text = before + "\n".join(lines) + rest.split(END, 1)[1]
    else:
        text += "\n" + "\n".join(lines) + "\n"
    README.write_text(text, encoding="utf-8")
    print(f"{passed}/{len(results)} passed; README updated")
    sys.exit(0 if outcome.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
