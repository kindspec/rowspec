# SPDX-License-Identifier: Apache-2.0 OR MIT
"""rowspec check — the specification's refusals, runnable on real files.

`.mdtbl` files go through the full parser and evaluator. `.csv` and `.tsv`
files go through CSV mode, which runs every refusal that a file nobody migrated
can support, plus the ones an adjacent `<file>.rowspec.json` unlocks.

Errors name entities, never offsets. `duplicate key id='r_01'` can be pasted
into a pull-request comment and acted on; "error at line 7" cannot, because
line 7 moves the moment anyone else edits the file.
"""

import argparse
import errno
import os
import stat
import sys
import tempfile

from . import edit
from .csvmode import Finding, check_file
from .sidecar import _undecodable_line
from .table import Malformed, _why_not_a_number, canon, evaluate, parse

CSV_EXT = (".csv", ".tsv", ".tab")
TABLE_EXT = (".mdtbl",)
SKIP_DIRS = {".git", ".cache", "node_modules", ".venv", "__pycache__"}


class _TableRefusal(Finding):
    """A refusal that stopped a file being read, carrying its SPEC §9
    identifier, or None for one that is not a §9 refusal."""

    def __init__(self, message, refusal):
        super().__init__("refused", message)
        self.refusal = refusal


def _code(refusal):
    return f" [{refusal}]" if refusal else ""


def _not_utf8(path, e):
    """The refusal for a `.mdtbl` that is not UTF-8, which the CLI decodes
    itself. `check` and `eval` both build it here, so they say the same. By
    content, never by offset (#234): the first line holding such a byte,
    quoted as a sidecar's message quotes it (#216), and the byte."""
    return _TableRefusal(
        f"not valid UTF-8: the line {_undecodable_line(path)} holds byte "
        f"0x{e.object[e.start]:02X}, which is not part of a valid sequence "
        f"({e.reason})",
        "bad-encoding",
    )


def _unreadable(path, e):
    """A file that could not be read or written (#246, #243): the operating
    system's reason, and the file it is about when that is not `path`
    itself, such as a sidecar."""
    other = e.filename if e.filename not in (None, path) else None
    return _TableRefusal(e.strerror + (f": {other}" if other else ""), None)


def validate(path: str) -> list[Finding]:
    """Every finding for one file. A refusal that stops the file being read at
    all arrives as a Malformed and becomes a single finding."""
    if path.lower().endswith(CSV_EXT):
        try:
            return check_file(path)
        except Malformed as e:
            return [_TableRefusal(str(e), e.refusal)]
        except OSError as e:
            return [_unreadable(path, e)]
    try:
        text = open(path, encoding="utf-8", newline="").read()
    except UnicodeDecodeError as e:
        return [_not_utf8(path, e)]
    except OSError as e:
        return [_unreadable(path, e)]
    try:
        evaluate(text)
    except Malformed as e:
        return [_TableRefusal(str(e), e.refusal)]
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
        print(f"{path}: {tag}{f}{_code(getattr(f, 'refusal', None))}", file=out)
        if f.detail and f.rule not in explained:
            explained.add(f.rule)
            print(f"    {f.detail}", file=out)


def _gh_data(s):
    """A workflow command's message, escaped as GitHub requires."""
    return s.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _gh_prop(s):
    """A workflow command's property value, such as `file=`."""
    return _gh_data(s).replace(":", "%3A").replace(",", "%2C")


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
        title = "rowspec" + _code(getattr(f, "refusal", None))
        print(f"::{kind} file={_gh_prop(path)},title={_gh_prop(title)}::{_gh_data(msg)}", file=out)


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
        except (Malformed, UnicodeDecodeError, OSError) as e:
            if isinstance(e, OSError):
                # Any file eval could not read, named or found in a
                # directory, even a `.csv` it would otherwise skip.
                found = _unreadable(path, e)
            elif not path.lower().endswith(TABLE_EXT):
                continue  # `eval` is for tables; `check` owns everything else
            elif isinstance(e, UnicodeDecodeError):
                found = _not_utf8(path, e)
            else:
                found = _TableRefusal(str(e), e.refusal)
            if fmt == "github":
                _print_github(path, [found], None, out)
            else:
                print(f"{path}: {found}{_code(found.refusal)}", file=sys.stderr)
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
                    msg = (
                        f"{where}{col} = {v} — a computed value did not resolve."
                        " `check` does not see this: the file is well formed and"
                        " its total is wrong."
                    )
                    print(f"::error file={_gh_prop(path)},title=rowspec::{_gh_data(msg)}", file=out)
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


def _keep_metadata(real, tmp, st):
    """Give the temporary file what the target had that a rename would lose
    (#248): its group, where this user may set it, its permission bits, and
    its extended attributes, which on Linux hold POSIX ACLs. Not its times,
    because the file has been edited, and not its owner, which only root may
    give away."""
    try:
        os.chown(tmp, -1, st.st_gid)
    except PermissionError:
        pass
    os.chmod(tmp, stat.S_IMODE(st.st_mode))
    if not hasattr(os, "listxattr"):
        return
    skip = (errno.ENOTSUP, errno.EOPNOTSUPP, errno.EPERM)
    try:
        names = os.listxattr(real)
    except OSError as e:
        if e.errno in skip:
            return
        raise
    for name in names:
        try:
            os.setxattr(tmp, name, os.getxattr(real, name))
        except OSError as e:
            if e.errno not in skip:
                raise


def _write(path, text):
    """Replace `path`'s contents with `text`, all or nothing (#248).

    `open(path, "w")` truncates at once, and a write that then fails, on a
    full disk say, reports its error only when the file is closed -- which a
    bare `open(...).write(...)` leaves to a finalizer that swallows it. So
    the text goes to a temporary file in the target's own directory, is
    flushed to disk, is given the target's metadata, and is renamed over the
    target; on any error, or an interrupt, the temporary file is removed
    and the target is left as it was. A symbolic link is written through to
    the file it names. A target this user cannot write is refused with the
    operating system's own reason, read-only file system included, as a
    plain write would refuse it. A hard link to the target does not see the
    edit: the rename gives `path` a new inode."""
    real = os.path.realpath(path)
    try:
        st = os.stat(real)
        os.close(os.open(real, os.O_WRONLY))  # probe only: opens, never truncates
    except OSError as e:
        raise OSError(e.errno, e.strerror, path) from None
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(real), prefix=".rowspec-", suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        _keep_metadata(real, tmp, st)
        os.replace(tmp, real)
    except BaseException as e:
        if tmp is not None and os.path.lexists(tmp):
            os.unlink(tmp)
        if isinstance(e, OSError):  # named by `path`, never by the temporary file
            raise OSError(e.errno, e.strerror, path) from None
        raise


def _rewrite(path, change, out, done):
    """Read `path`, apply `change` to its text, and write the result back. A
    refused edit raises before anything is written, so the file is untouched.
    A refusal with an identifier, a §9 one or the editing API's own reason,
    is printed with it, so a program can read it without parsing the
    message; a file that cannot be read or written is named with the
    operating system's reason, and carries none."""
    try:
        text = open(path, encoding="utf-8", newline="").read()
        new, what = change(text)
        _write(path, new)
    except OSError as e:  # missing, a directory, read-only: name the file
        print(f"{path}: {_unreadable(path, e)}", file=sys.stderr)
        return 1
    except UnicodeDecodeError as e:
        f = _not_utf8(path, e)  # check's refusal, line and identifier
        print(f"{path}: {f}{_code(f.refusal)}", file=sys.stderr)
        return 1
    except Malformed as e:
        code = e.refusal or getattr(e, "reason", None)
        print(f"{path}: {e}" + (f" [{code}]" if code else ""), file=sys.stderr)
        return 1
    print(f"{path}: {done(what)}", file=out or sys.stdout)
    return 0


def cmd_add_row(path, values, out=None, *, rid=None, after=None, before=None, end=False):
    """Add a row, minting the opaque id §6 requires unless one is given.

    The spec insists row ids are machine-generated; before this, they were hand
    typed, which is how a cross-branch id collision got made by hand. `rid`
    chooses the id instead. With no position the row goes where its key sorts
    when the rows are already in key order, and at the end otherwise: two
    concurrent appends at the end always collide. `after`/`before` place it
    beside a key, and `end` at the end.
    """

    def change(text):
        cols, formulas, _r, _d, _o, key = parse(text)
        if key is None:
            raise Malformed("no `key :=` declaration, so there is no id to mint")
        fillable = [c for c in cols if c != key and c not in formulas]
        if len(values) != len(fillable):
            raise Malformed(
                f"expected {len(fillable)} value(s) for {', '.join(fillable)}; got {len(values)}"
            )
        new, got = edit.insert_row(
            text,
            dict(zip(fillable, values, strict=True)),
            id=rid,
            after=after,
            before=before,
            end=end,
        )
        return new, f"{key}={got}"

    return _rewrite(path, change, out, lambda what: f"added {what}")


COMMANDS = {
    "check": "validate .csv, .tsv and .mdtbl tables (the default command)",
    "eval": "print computed values, and fail on any #REF!",
    "add-row": "add a row with a minted or chosen id, where its key sorts or beside a key",
    "add-column": "add a stored or computed column, editing every row",
    "delete-column": "delete a column that no formula or declaration names",
    "rename-column": "rename a column everywhere a formula or declaration names it",
}


def _help():
    width = max(len(c) for c in COMMANDS)
    lines = [f"  {c:<{width}}  {d}" for c, d in COMMANDS.items()]
    return (
        "usage: rowspec [COMMAND] [-h] ...\n\n"
        "Validate, evaluate and edit rowspec tables.\n\n"
        "commands:\n" + "\n".join(lines) + "\n\n"
        "Without a command, rowspec runs check. `rowspec COMMAND --help` describes one."
    )


def _parser(cmd):
    p = argparse.ArgumentParser(prog=f"rowspec {cmd}", description=COMMANDS[cmd])
    if cmd in ("check", "eval"):
        # `eval` accepts check's options and ignores all but --format; they
        # stay accepted so no existing command line breaks, and stay out of
        # its help, which would otherwise describe options that do nothing.
        quiet = argparse.SUPPRESS if cmd == "eval" else None
        p.add_argument("paths", nargs="+", help="files or directories")
        p.add_argument(
            "--fmt", action="store_true", help=quiet or "rewrite .mdtbl files into canonical form"
        )
        p.add_argument(
            "--fmt-check",
            action="store_true",
            help=quiet or "report files that are not in canonical form, without rewriting them",
        )
        p.add_argument(
            "--strict",
            action="store_true",
            help=quiet or "treat warnings (CRLF, BOM, lone CR) as refusals",
        )
        p.add_argument(
            "--format", choices=("plain", "github"), default="plain", help="output format"
        )
        return p
    p.add_argument("file", help="the .mdtbl file to edit in place")
    if cmd == "add-row":
        p.add_argument(
            "values",
            nargs="*",
            help="one value per stored column other than the key, in header order",
        )
        p.add_argument("--id", help="the new row's id, instead of a minted one")
    elif cmd == "add-column":
        p.add_argument("name", help="the new column's name")
        p.add_argument("--formula", help="make it a computed column with this formula")
        p.add_argument("--value", default="", help="the value of every cell of a stored column")
        p.add_argument(
            "--align",
            default="---",
            help="the alignment cell (default ---); a value starting with - is written "
            "with =, as in --align=--:",
        )
    elif cmd == "delete-column":
        p.add_argument("name", help="the column to delete")
    elif cmd == "rename-column":
        p.add_argument("old", help="the column's name")
        p.add_argument("new", help="its new name")
    if cmd in ("add-row", "add-column"):
        what = "row's key" if cmd == "add-row" else "column"
        where = p.add_mutually_exclusive_group()
        where.add_argument(
            "--after",
            metavar="KEY" if cmd == "add-row" else "COLUMN",
            help=f"place it after this {what}",
        )
        where.add_argument(
            "--before",
            metavar="KEY" if cmd == "add-row" else "COLUMN",
            help=f"place it before this {what}",
        )
        if cmd == "add-row":
            where.add_argument(
                "--end",
                action="store_true",
                help="place it last; without a position, it goes where its key sorts "
                "if the rows are in key order, and last otherwise",
            )
    return p


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] in (["-h"], ["--help"]):
        print(_help())
        return 0
    # Pull the subcommand off BEFORE argparse. Leaving it as a `nargs="?"`
    # positional beside a `nargs="+"` one made argparse mis-split
    # `eval --format github DIR` -- it reported "unrecognized arguments: DIR"
    # and the same line worked only with the option written after the path.
    cmd = "check"
    if argv and argv[0] in COMMANDS:
        cmd = argv.pop(0)
    p = _parser(cmd)
    a = p.parse_args(argv)
    if getattr(a, "file", None) == "":
        p.error("the file name is empty")
    if "" in getattr(a, "paths", ()):  # most often an unset variable (#250)
        p.error("a path is empty")
    if cmd == "eval":
        return cmd_eval(a.paths, fmt=a.format)
    if cmd == "add-row":
        return cmd_add_row(a.file, a.values, rid=a.id, after=a.after, before=a.before, end=a.end)
    if cmd == "add-column":
        return _rewrite(
            a.file,
            lambda t: (
                edit.add_column(
                    t,
                    a.name,
                    formula=a.formula,
                    value=a.value,
                    after=a.after,
                    before=a.before,
                    align=a.align,
                ),
                a.name,
            ),
            sys.stdout,
            lambda n: f"added column {n}",
        )
    if cmd == "delete-column":
        return _rewrite(
            a.file,
            lambda t: (edit.delete_column(t, a.name), a.name),
            sys.stdout,
            lambda n: f"deleted column {n}",
        )
    if cmd == "rename-column":
        return _rewrite(
            a.file,
            lambda t: (edit.rename_column(t, a.old, a.new), a.new),
            sys.stdout,
            lambda n: f"renamed column {a.old} to {n}",
        )
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
                    emit(
                        f,
                        [Finding("not-canonical", "not in canonical form (run --fmt)")],
                        explained,
                        sys.stderr,
                    )
                    refused += 1
                else:
                    try:
                        _write(f, c)
                    except OSError as e:
                        emit(f, [_unreadable(f, e)], explained, sys.stderr)
                        refused += 1
                    else:
                        print(f"{f}: reformatted")

    summary = f"{len(files)} file(s) checked, {refused} refused"
    if warned:
        summary += f", {warned} with warnings"
    print(summary)
    return 1 if refused else 0
