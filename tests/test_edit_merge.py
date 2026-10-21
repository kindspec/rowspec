# SPDX-License-Identifier: Apache-2.0 OR MIT
"""`rowspec.edit` through real `git merge`: two branches each make one edit,
and the merged file is compared with the two edits applied one after the
other.

The outcome of each pairing is pinned. A clean merge must evaluate to what
applying both edits serially gives, in one order or the other, or differ only
by a `#REF!` that `rowspec eval` reports. A pairing that merges cleanly to a
different value with no `#REF!` is the failure the format exists to prevent,
and no scenario here may produce one.
"""

import os
import subprocess
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

from rowspec import Malformed, edit, evaluate, parse, render, set_cell, structure  # noqa: E402

BASE = (
    "| id | item | region | qty | unit | total = qty * unit |\n"
    "| --- | --- | --- | --: | --: | --: |\n"
    "| r_01 | widget | EU | 10 | 12.00 |  |\n"
    "| r_02 | gadget | US | 3 | 4.50 |  |\n"
    "| r_03 | bolt | EU | 100 | 0.10 |  |\n"
    "| r_04 | nut | US | 200 | 0.05 |  |\n"
    "| r_05 | gear | EU | 7 | 9.00 |  |\n"
    "| r_06 | cog | US | 5 | 2.00 |  |\n"
    "\n"
    "key := id\n"
    "grand := sum(total)\n"
    'eu := sum(total where region = "EU")\n'
)

PADDED = (
    "| id   | item   | region | qty | unit  | total = qty * unit |\n"
    "| ---- | ------ | ------ | --: | ----: | -----------------: |\n"
    "| r_01 | widget | EU     |  10 | 12.00 |                    |\n"
    "| r_02 | gadget | US     |   3 |  4.50 |                    |\n"
    "| r_03 | bolt   | EU     | 100 |  0.10 |                    |\n"
    "| r_04 | nut    | US     | 200 |  0.05 |                    |\n"
    "| r_05 | gear   | EU     |   7 |  9.00 |                    |\n"
    "| r_06 | cog    | US     |   5 |  2.00 |                    |\n"
    "\n"
    "key := id\n"
    "grand := sum(total)\n"
)


_IDS = iter(range(10, 1000))


def ins(after=None, before=None, rid=None, item="new", end=False):
    """An insertion with a fixed id, so that applying it twice, once on a
    branch and once serially, inserts the same row."""
    rid = rid or f"r_{next(_IDS)}"
    return lambda t: edit.add_row(
        t,
        {"item": item, "region": "EU", "qty": "1", "unit": "1"},
        row_key=rid,
        after=after,
        before=before,
        end=end,
    )[0]


def cell(rid, col, value):
    def op(t):
        st = structure(t)
        set_cell(st, rid, col, value)
        return render(st)

    return op


def realign(text):
    """Re-pad every table line to the widest cell of each column: what a
    formatter that keeps a table aligned does after any edit."""
    lines = text.split("\n")
    tbl = [i for i, ln in enumerate(lines) if ln.startswith("|")]
    cells = [[c.strip() for c in lines[i].strip("|").split("|")] for i in tbl]
    widths = [max(len(r[k]) for r in cells) for k in range(len(cells[0]))]
    for i, r in zip(tbl, cells, strict=True):
        if i == tbl[1]:
            r = [c[0] + "-" * (w - 2) + c[-1] for c, w in zip(r, widths, strict=True)]
        lines[i] = "| " + " | ".join(c.ljust(w) for c, w in zip(r, widths, strict=True)) + " |"
    return "\n".join(lines)


# name: (base, branch A's edit, branch B's edit, the outcome)
SCENARIOS = {
    "insert after r_01 / insert after r_04": (BASE, ins("r_01"), ins("r_04"), "clean"),
    "insert after r_02 / insert before r_03": (BASE, ins("r_02"), ins(before="r_03"), "conflict"),
    "insert at end / insert at end": (BASE, ins(end=True), ins(end=True), "conflict"),
    "insert after r_01 / insert at end": (BASE, ins("r_01"), ins(end=True), "clean"),
    # The default: where the key sorts, since BASE's rows are in key order.
    "insert r_015 / insert r_045, by key": (
        BASE,
        ins(rid="r_015"),
        ins(rid="r_045"),
        "clean",
    ),
    "insert r_021 / insert r_025, by key (same gap)": (
        BASE,
        ins(rid="r_021"),
        ins(rid="r_025"),
        "conflict",
    ),
    "insert r_07 after r_01 / insert r_07 after r_04": (
        BASE,
        ins("r_01", rid="r_07"),
        ins("r_04", rid="r_07", item="x"),
        "refused",
    ),
    "insert after r_03 / edit r_03": (BASE, ins("r_03"), cell("r_03", "qty", "9"), "conflict"),
    "insert after r_03 / edit r_04": (BASE, ins("r_03"), cell("r_04", "qty", "9"), "conflict"),
    "insert after r_01 / edit r_04": (BASE, ins("r_01"), cell("r_04", "qty", "9"), "clean"),
    "delete r_02 / edit r_02": (
        BASE,
        lambda t: edit.delete_row(t, "r_02"),
        cell("r_02", "qty", "9"),
        "conflict",
    ),
    "delete r_02 / edit r_03": (
        BASE,
        lambda t: edit.delete_row(t, "r_02"),
        cell("r_03", "qty", "9"),
        "conflict",
    ),
    "delete r_02 / edit r_05": (
        BASE,
        lambda t: edit.delete_row(t, "r_02"),
        cell("r_05", "qty", "9"),
        "clean",
    ),
    "delete r_02 / delete r_02": (
        BASE,
        lambda t: edit.delete_row(t, "r_02"),
        lambda t: edit.delete_row(t, "r_02"),
        "clean",
    ),
    "delete r_02 / delete r_05": (
        BASE,
        lambda t: edit.delete_row(t, "r_02"),
        lambda t: edit.delete_row(t, "r_05"),
        "clean",
    ),
    "delete r_03 / insert after r_03": (
        BASE,
        lambda t: edit.delete_row(t, "r_03"),
        ins("r_03"),
        "conflict",
    ),
    "edit r_01 / edit r_02": (BASE, cell("r_01", "qty", "9"), cell("r_02", "qty", "9"), "conflict"),
    "edit r_01 / edit r_03": (BASE, cell("r_01", "qty", "9"), cell("r_03", "qty", "9"), "clean"),
    "rename qty / insert row": (
        BASE,
        lambda t: edit.rename_column(t, "qty", "quantity"),
        ins("r_03"),
        "clean",
    ),
    "rename qty / edit r_03 qty": (
        BASE,
        lambda t: edit.rename_column(t, "qty", "quantity"),
        cell("r_03", "qty", "9"),
        "clean",
    ),
    "rename region / delete r_01": (
        BASE,
        lambda t: edit.rename_column(t, "region", "area"),
        lambda t: edit.delete_row(t, "r_01"),
        "clean",
    ),
    "rename qty / rename unit": (
        BASE,
        lambda t: edit.rename_column(t, "qty", "quantity"),
        lambda t: edit.rename_column(t, "unit", "price"),
        "conflict",
    ),
    "rename qty / set formula": (
        BASE,
        lambda t: edit.rename_column(t, "qty", "quantity"),
        lambda t: edit.set_formula(t, "total", "qty * unit * 2"),
        "conflict",
    ),
    "rename qty / new declaration naming qty": (
        BASE,
        lambda t: edit.rename_column(t, "qty", "quantity"),
        lambda t: edit.set_declaration(t, "q", "sum(qty)"),
        "order-dependent #REF!",
    ),
    "rename region / edit eu declaration": (
        BASE,
        lambda t: edit.rename_column(t, "region", "area"),
        lambda t: edit.set_declaration(t, "eu", 'sum(qty where region = "EU")'),
        "conflict",
    ),
    "add column / insert row": (
        BASE,
        lambda t: edit.add_column(t, "note"),
        ins("r_03"),
        "conflict",
    ),
    "add column / edit r_03": (
        BASE,
        lambda t: edit.add_column(t, "note"),
        cell("r_03", "qty", "9"),
        "conflict",
    ),
    "add column / new declaration": (
        BASE,
        lambda t: edit.add_column(t, "note"),
        lambda t: edit.set_declaration(t, "n", "count(id)"),
        "clean",
    ),
    "delete column item / edit r_03 item": (
        BASE,
        lambda t: edit.delete_column(t, "item"),
        cell("r_03", "item", "x"),
        "conflict",
    ),
    "delete column item / new declaration naming item": (
        BASE,
        lambda t: edit.delete_column(t, "item"),
        lambda t: edit.set_declaration(t, "n", "count(item)"),
        "clean #REF!",
    ),
    "set formula / insert row": (
        BASE,
        lambda t: edit.set_formula(t, "total", "qty * unit * 2"),
        ins("r_03"),
        "clean",
    ),
    "replace grand / replace eu": (
        BASE,
        lambda t: edit.set_declaration(t, "grand", "max(total)"),
        lambda t: edit.set_declaration(t, "eu", "min(total)"),
        "conflict",
    ),
    "new declaration / new declaration": (
        BASE,
        lambda t: edit.set_declaration(t, "n", "count(id)"),
        lambda t: edit.set_declaration(t, "m", "max(qty)"),
        "conflict",
    ),
    "delete eu / rename region": (
        BASE,
        lambda t: edit.delete_declaration(t, "eu"),
        lambda t: edit.rename_column(t, "region", "area"),
        "conflict",
    ),
    "padded: wide insert after r_01 / insert after r_04": (
        PADDED,
        ins("r_01", item="a much longer item"),
        ins("r_04"),
        "clean",
    ),
    "padded: wide insert after r_01, re-aligned / insert after r_04": (
        PADDED,
        lambda t: realign(ins("r_01", item="a much longer item")(t)),
        ins("r_04"),
        "conflict",
    ),
}


def git(repo, *args, check=True):
    env = dict(
        os.environ,
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
        GIT_AUTHOR_NAME="t",
        GIT_AUTHOR_EMAIL="t@example.invalid",
        GIT_COMMITTER_NAME="t",
        GIT_COMMITTER_EMAIL="t@example.invalid",
    )
    return subprocess.run(
        ["git", "-C", str(repo), *args], env=env, capture_output=True, text=True, check=check
    )


def snapshot(text):
    """What a file means: its columns, each row's values by id, its aggregates.
    A refusal is its identifier."""
    try:
        seq, aggs = evaluate(text)
    except Malformed as e:
        return ("refused", e.refusal)
    cols, *_r, key = parse(text)
    return (tuple(cols), {r[key]: r for r in seq}, aggs)


def serial(base, a, b):
    try:
        return snapshot(b(a(base)))
    except Malformed as e:
        return ("refused", getattr(e, "reason", None) or e.refusal)


def refs(snap):
    """The `#REF!` values a snapshot holds."""
    if snap[0] == "refused":
        return []
    vals = [*(v for r in snap[1].values() for v in r.values()), *snap[2].values()]
    return sorted({v for v in vals if isinstance(v, str) and v.startswith("#REF!")})


def merge(tmp_path, base, a, b):
    """(outcome, detail) for edits `a` and `b` made on two branches of `base`
    and merged with stock git. An outcome is `conflict`, `refused` (the merged
    file is), `clean` (it means what every serial order that is not refused
    means), `order-dependent` (what one order means and not the other), or
    `silently-wrong` (neither, with no `#REF!` to say so); a clean or
    order-dependent result holding a `#REF!` the base did not is suffixed
    ` #REF!`."""
    repo = tmp_path / "repo"
    git(tmp_path, "init", "-q", "-b", "main", str(repo))
    f = repo / "t.mdtbl"

    def commit(text, msg):
        f.write_text(text, encoding="utf-8", newline="")
        git(repo, "add", "t.mdtbl")
        git(repo, "commit", "-q", "-m", msg)

    commit(base, "base")
    git(repo, "checkout", "-q", "-b", "a")
    commit(a(base), "a")
    git(repo, "checkout", "-q", "-b", "b", "main")
    commit(b(base), "b")
    if git(repo, "merge", "-q", "--no-edit", "a", check=False).returncode:
        return "conflict", None
    merged = snapshot(f.read_text(encoding="utf-8"))
    if merged[0] == "refused":
        return "refused", merged[1]
    orders = {"a-then-b": serial(base, a, b), "b-then-a": serial(base, b, a)}
    valid = {k: v for k, v in orders.items() if v[0] != "refused"}
    new_refs = [r for r in refs(merged) if r not in refs(snapshot(base))]
    suffix = " #REF!" if new_refs else ""
    detail = {
        k: ("same" if v == merged else v[1] if v[0] == "refused" else "differs")
        for k, v in orders.items()
    }
    if not valid:
        # Both orders refuse: each branch made the change the other would
        # then be refused for, such as deleting the same row twice.
        same = merged in (snapshot(a(base)), snapshot(b(base)))
        return ("clean" if same else "silently-wrong") + suffix, detail
    hits = [k for k, v in valid.items() if v == merged]
    if len(hits) == len(valid):
        return "clean" + suffix, detail
    if hits:
        return "order-dependent" + suffix, detail
    return ("loud" if new_refs else "silently-wrong"), detail


@pytest.mark.parametrize("name", list(SCENARIOS))
def test_merge_outcome(tmp_path, name):
    base, a, b, want = SCENARIOS[name]
    got, _detail = merge(tmp_path, base, a, b)
    assert got == want


def test_a_merge_that_means_neither_order_is_reported(tmp_path):
    """The control for the outcomes above: an edit that writes something
    different on its branch from what it writes when replayed serially gives a
    merged file that means neither order, and `merge` must say so rather than
    call it clean."""
    calls = iter(["1", "2", "2", "2"])

    def a(t):
        return edit.add_row(t, {"qty": next(calls), "unit": "1"}, row_key="r_99")[0]

    got, _detail = merge(tmp_path, BASE, a, lambda t: edit.delete_row(t, "r_02"))
    assert got == "silently-wrong"


def measure_concurrent_inserts(tmp, ids, rng, pairs=100, end=False):
    """{outcome: count} for `pairs` pairs of rows inserted on two branches of a
    table whose rows have `ids`, in that order, each new row with a random id of
    the shape `add_row` generates, placed by default or at the end."""
    import pathlib

    base = "| id | qty |\n| --- | --: |\n" + "".join(f"| {i} | 1 |\n" for i in ids)
    base += "\nkey := id\ns := sum(qty)\n"
    counts = {}
    for n in range(pairs):
        a, b = (f"r_{rng.getrandbits(24):06x}" for _ in range(2))
        ops = [
            (lambda t, r=r: edit.add_row(t, {"qty": "1"}, row_key=r, end=end)[0]) for r in (a, b)
        ]
        d = pathlib.Path(tmp) / f"{id(counts)}-{n}"
        d.mkdir()
        got, _ = merge(d, base, *ops)
        counts[got] = counts.get(got, 0) + 1
    return counts


def concurrent_insert_table(tmp):
    """The measurement docs/editing-api.md quotes. Run
    `uv run python tests/test_edit_merge.py` to print it."""
    import random

    out = []
    for seed in (1, 7):
        rng = random.Random(seed)
        rand = sorted(f"r_{rng.getrandbits(24):06x}" for _ in range(50))
        out.append(
            (
                f"50 random-shape ids in key order, seed {seed}, at the end",
                measure_concurrent_inserts(tmp, rand, rng, end=True),
            )
        )
        out.append(
            (
                f"50 random-shape ids in key order, seed {seed}, by key",
                measure_concurrent_inserts(tmp, rand, rng),
            )
        )
    rng = random.Random(1)
    rand = sorted(f"r_{rng.getrandbits(24):06x}" for _ in range(50))
    swapped = list(rand)
    swapped[10], swapped[11] = swapped[11], swapped[10]
    appended = [f"r_{rng.getrandbits(24):06x}" for _ in range(50)]
    for label, ids in (
        ("50 sequential ids r_0001..r_0050, by key", [f"r_{i:04d}" for i in range(1, 51)]),
        ("50 random-shape ids, one adjacent pair swapped, by key", swapped),
        ("50 random-shape ids in the order they were appended, by key", appended),
        ("no rows, by key", []),
    ):
        out.append((label, measure_concurrent_inserts(tmp, ids, rng)))
    return out


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        for label, counts in concurrent_insert_table(tmp):
            print(f"{label}: {counts}", flush=True)
