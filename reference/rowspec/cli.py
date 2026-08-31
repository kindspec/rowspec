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
from .table import Malformed, _why_not_a_number, canon, escape_cell, evaluate, parse

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
        text = open(path, encoding="utf-8", newline="").read()
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


def _offending_cell(rows, col):
    """The first cell in `col` that will not parse as a number, if any."""
    from .table import num

    for r in rows:
        v = r.get(col)
        if v in ("", None) or not isinstance(v, str):
            continue
        try:
            num(v)
        except (ValueError, TypeError):
            return v
    return None


def _fmt_value(v):
    if isinstance(v, float):
        if v == int(v):
            return f"{int(v)}"
        r = round(v, 10)
        return f"{r:.10f}".rstrip("0").rstrip(".")
    return "" if v is None else str(v)


def cmd_eval(paths, out=sys.stdout, fmt="plain") -> int:
    """Print computed columns and aggregates, and FAIL on any #REF!.

    Validation alone reports "0 refused" on a table whose total is wrong: a
    misspelled column, a thousands separator and a non-ASCII space all become
    #REF! under §8 and are correctly NOT §9 refusals. Without this command the
    one thing the format does that a CSV cannot is invisible, and a CI recipe
    built on `check` is green on a broken total.
    """
    bad = 0
    for path in collect(paths):
        try:
            rows, aggs = evaluate(open(path, encoding="utf-8", newline="").read())
            cols, formulas, _r, decls, _o, _k = parse(
                open(path, encoding="utf-8", newline="").read()
            )
        except Malformed as e:
            if not path.lower().endswith(TABLE_EXT):
                continue  # `eval` is for tables; `check` owns everything else
            print(f"{path}: {e}", file=sys.stderr)
            bad += 1
            continue

        refs = []
        computed = [c for c in cols if c in formulas]
        print(f"{path}", file=out)
        if computed and rows:
            kw = max(len(str(r.get(_k, ""))) for r in rows) if _k else 0
            cw = max(len(c) for c in computed)
            for r in rows:
                cells = []
                for c in computed:
                    v = r.get(c)
                    if isinstance(v, str) and v.startswith("#REF!"):
                        refs.append((r.get(_k) if _k else "?", c, v))
                    cells.append(f"{c}={_fmt_value(v):>{cw}}")
                rk = f"{str(r.get(_k, '')):<{kw}}  " if _k else ""
                print(f"    {rk}{'  '.join(cells)}", file=out)
        for name, v in aggs.items():
            marker = "  <-- ERROR" if isinstance(v, str) and v.startswith("#REF!") else ""
            print(f"    {name} = {_fmt_value(v)}{marker}", file=out)
            if marker:
                refs.append((None, name, v))
        if refs:
            bad += 1
            if fmt == "github":
                # Without this, `eval` failures reach CI as a bare exit code
                # with nothing attached to a file, so the one thing this format
                # does that a CSV cannot is invisible in the place it matters.
                for rowkey, col, v in refs:
                    where = f"row {rowkey}, " if rowkey is not None else ""
                    print(
                        f"::error file={path},title=rowspec::{where}{col} = {v}"
                        f" — a computed value did not resolve. `check` does not"
                        f" see this: the file is well formed and its total is"
                        f" wrong.",
                        file=out,
                    )
            print(f"  {len(refs)} unresolved reference(s):", file=sys.stderr)
            seen = set()
            for rowkey, col, v in refs:
                sig = (col, v)
                if sig in seen:
                    continue
                seen.add(sig)
                where = f"row {rowkey}, " if rowkey else ""
                print(f"    {where}{col} = {v}", file=sys.stderr)
                name = v[len("#REF!(") : -1] if v.startswith("#REF!(") else ""
                cell = _offending_cell(rows, name)
                if cell is not None:
                    print(f"        {_why_not_a_number(cell)}", file=sys.stderr)
    return 1 if bad else 0


def cmd_add_row(path: str, values: list[str], out=sys.stdout) -> int:
    """Append a row, minting the opaque id §6 requires and nothing produced.

    The spec insists row ids are machine-generated; before this, they were hand
    typed, which is how a cross-branch id collision got made by hand.
    """
    import secrets

    text = open(path, encoding="utf-8", newline="").read()
    cols, formulas, rows, _d, _o, key = parse(text)
    if key is None:
        print(f"{path}: no `key :=` declaration, so there is no id to mint", file=sys.stderr)
        return 1
    taken = {str(r.get(key)) for r in rows}
    while True:
        rid = "r_" + secrets.token_hex(3)
        if rid not in taken:
            break
    fillable = [c for c in cols if c != key and c not in formulas]
    if len(values) != len(fillable):
        print(
            f"{path}: expected {len(fillable)} value(s) for {', '.join(fillable)}; "
            f"got {len(values)}",
            file=sys.stderr,
        )
        return 1
    supplied = dict(zip(fillable, values, strict=True))
    cells = [rid if c == key else "" if c in formulas else supplied.get(c, "") for c in cols]
    line = "| " + " | ".join(escape_cell(c) for c in cells) + " |"
    lines = text.splitlines(keepends=True)
    last = max(i for i, ln in enumerate(lines) if ln.strip().startswith("|"))
    eol = "\r\n" if lines[last].endswith("\r\n") else "\n"
    lines.insert(last + 1, line + eol)
    open(path, "w", encoding="utf-8", newline="").write("".join(lines))
    print(f"{path}: added {key}={rid}", file=out)
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    # Pull the subcommand off BEFORE argparse. Leaving it as a `nargs="?"`
    # positional beside a `nargs="+"` one made argparse mis-split
    # `eval --format github DIR` -- it reported "unrecognized arguments: DIR"
    # and the same line worked only with the option written after the path.
    cmd = "check"
    if argv and argv[0] in ("check", "eval", "add-row"):
        cmd = argv.pop(0)

    p = argparse.ArgumentParser(
        prog="rowspec check", description="Validate .csv, .tsv and .mdtbl tables."
    )
    p.add_argument("paths", nargs="+", help="files or directories")
    p.add_argument("--fmt", action="store_true", help="rewrite .mdtbl files into canonical form")
    p.add_argument(
        "--fmt-check",
        action="store_true",
        help="report files that are not in canonical form, without rewriting them",
    )
    p.add_argument("--strict", action="store_true", help="treat warnings (CRLF, BOM) as refusals")
    p.add_argument("--format", choices=("plain", "github"), default="plain", help="output format")
    a = p.parse_args(argv)
    if cmd == "eval":
        return cmd_eval(a.paths, fmt=a.format)
    if cmd == "add-row":
        return cmd_add_row(a.paths[0], a.paths[1:])

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
        elif (a.fmt or a.fmt_check) and f.lower().endswith(TABLE_EXT):
            text = open(f, encoding="utf-8", newline="").read()
            c = canon(text)
            if c != text:
                if a.fmt_check:
                    print(f"{f}: not in canonical form (run --fmt)", file=sys.stderr)
                    refused += 1
                else:
                    open(f, "w", encoding="utf-8", newline="").write(c)
                    print(f"{f}: reformatted")

    summary = f"{len(files)} file(s) checked, {refused} refused"
    if warned:
        summary += f", {warned} with warnings"
    print(summary)
    return 1 if refused else 0
