"""rowspec check — the specification's refusals, runnable on real files.

`.mdtbl` files go through the full parser and evaluator. `.csv` and `.tsv`
files go through CSV mode, which runs every refusal that a file nobody migrated
can support, plus the ones an adjacent `<file>.rowspec.json` unlocks.

Errors name entities, never offsets. `duplicate key id='r_01'` can be pasted
into a pull-request comment and acted on; "error at line 7" cannot, because
line 7 moves the moment anyone else edits the file.
"""

import argparse
import os
import sys

from .csvmode import Finding, check_file
from .table import Malformed, canon, evaluate

CSV_EXT = (".csv", ".tsv", ".tab")
TABLE_EXT = (".mdtbl",)
SKIP_DIRS = {".git", ".cache", "node_modules", ".venv", "__pycache__"}


def validate(path: str) -> list[Finding]:
    """Every finding for one file. A refusal that stops the file being read at
    all arrives as a Malformed and becomes a single finding."""
    if path.lower().endswith(CSV_EXT):
        try:
            return check_file(path)
        except Malformed as e:
            return [Finding("refused", str(e))]
    try:
        text = open(path, encoding="utf-8").read()
    except UnicodeDecodeError as e:
        return [Finding("encoding", f"not valid UTF-8: {e}")]
    try:
        evaluate(text)
    except Malformed as e:
        return [Finding("refused", str(e))]
    return []


def collect(targets: list[str]) -> list[str]:
    files: list[str] = []
    for target in targets:
        if os.path.isdir(target):
            for dp, dn, fn in os.walk(target):
                dn[:] = [d for d in dn if d not in SKIP_DIRS]
                files += [
                    os.path.join(dp, f) for f in fn if f.lower().endswith(CSV_EXT + TABLE_EXT)
                ]
        else:
            files.append(target)
    return sorted(files)


def _print_plain(path, findings, explained, out):
    for f in findings:
        tag = "" if f.level == "refuse" else "warning: "
        print(f"{path}: {tag}{f}", file=out)
        if f.detail and f.rule not in explained:
            explained.add(f.rule)
            print(f"    {f.detail}", file=out)


def _print_github(path, findings, explained, out):
    """GitHub Actions annotations. The message still names the entity; the file
    is the only location given, because a line number would be a coordinate and
    would be wrong by the time anyone reads it."""
    del explained
    for f in findings:
        kind = "error" if f.level == "refuse" else "warning"
        msg = str(f).replace("\n", " ")
        if f.detail:
            msg += " — " + f.detail
        print(f"::{kind} file={path},title=rowspec::{msg}", file=out)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "check":
        argv.pop(0)

    p = argparse.ArgumentParser(
        prog="rowspec check", description="Validate .csv, .tsv and .mdtbl tables."
    )
    p.add_argument("paths", nargs="+", help="files or directories to check")
    p.add_argument("--fmt", action="store_true", help="rewrite .mdtbl files into canonical form")
    p.add_argument("--strict", action="store_true", help="treat warnings (CRLF, BOM) as refusals")
    p.add_argument("--format", choices=("plain", "github"), default="plain", help="output format")
    a = p.parse_args(argv)

    files = collect(a.paths)
    emit = _print_github if a.format == "github" else _print_plain
    explained: set[str] = set()
    refused = warned = 0

    for f in files:
        findings = validate(f)
        errs = [x for x in findings if x.level == "refuse"]
        warns = [x for x in findings if x.level == "warn"]
        if a.strict:
            errs, warns = errs + warns, []
            for x in errs:
                x.level = "refuse"
        if errs or warns:
            emit(f, errs + warns, explained, sys.stderr)
        if errs:
            refused += 1
        elif warns:
            warned += 1
        elif a.fmt and f.lower().endswith(TABLE_EXT):
            text = open(f, encoding="utf-8").read()
            c = canon(text)
            if c != text:
                open(f, "w", encoding="utf-8").write(c)
                print(f"{f}: reformatted")

    summary = f"{len(files)} file(s) checked, {refused} refused"
    if warned:
        summary += f", {warned} with warnings"
    print(summary)
    return 1 if refused else 0
