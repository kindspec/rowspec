# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Every computed column is evaluated by dependency over one graph (§4.2 rule 9).

Ordinary formulas, `prior`/`delta`/`cumulative` and group aggregates are all
nodes of that graph. A row-relative column reads the values its source column
evaluates to, as numbers and errors, wherever that column stands in the header
and whatever kind of formula computes it. A cycle through a row-relative or
group column is a cycle like any other.

Unit tests of the two implementations, not conformance cases: the cases for
these rules come from an author who has not read `reference/`.
"""

import importlib
import itertools

import pytest

IMPLS = pytest.mark.parametrize("impl", ["rowspec.table", "rowspec_alt.table"])
ORDER = "\nkey := id\norder := by(id)\n"
CYCLE = "#REF!(cycle)"


def table(header, rows):
    cols = [h.strip() for h in header.strip("|").split("|")]
    lines = [header, "| " + " | ".join("--" for _ in cols) + " |"]
    for r in rows:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines) + "\n" + ORDER


def values(impl, src, *cols):
    rows, _ = importlib.import_module(impl).evaluate(src)
    return [[r[c] for c in cols] for r in rows]


# --- #112: a computed number is read as a number, not through its spelling --


@IMPLS
@pytest.mark.parametrize("op", ["/ 100000", "* 10000000000000000"], ids=["1e-05", "1e+16"])
def test_row_relative_over_a_computed_number_in_exponent_form(impl, op):
    src = table(
        f"| id | a | b = a {op} | p = prior(b) | d = delta(b) | c = cumulative(b) |",
        [["r_1", "1", "", "", "", ""], ["r_2", "2", "", "", "", ""], ["r_3", "3", "", "", "", ""]],
    )
    f = (lambda a: a / 100000) if op.startswith("/") else (lambda a: a * 10000000000000000)
    b = [f(1.0), f(2.0), f(3.0)]
    assert values(impl, src, "b", "p", "d", "c") == [
        [b[0], "", "", b[0]],
        [b[1], b[0], b[1] - b[0], b[0] + b[1]],
        [b[2], b[1], b[2] - b[1], b[0] + b[1] + b[2]],
    ]


# --- #113: a computed error keeps the name it originated with ----------------


@IMPLS
@pytest.mark.parametrize(
    "formula, first, second",
    [("a / z", "#REF!(/0)", 2.0), ("nope", "#REF!(nope)", "#REF!(nope)")],
    ids=["div-by-zero", "missing-name"],
)
def test_cumulative_carries_a_computed_sources_own_error(impl, formula, first, second):
    src = table(
        f"| id | a | z | b = {formula} | d = delta(b) | c = cumulative(b) |",
        [["r_1", "1", "0", "", "", ""], ["r_2", "2", "1", "", "", ""]],
    )
    assert values(impl, src, "b", "d", "c") == [
        [first, first, first],
        [second, first, first],
    ]


# --- #132: a source that does not resolve, or is on a cycle, in every row ----


@IMPLS
@pytest.mark.parametrize("fn", ["prior", "delta", "cumulative"])
@pytest.mark.parametrize("nrows", [1, 2])
def test_row_relative_over_a_missing_column_is_ref_in_every_row(impl, fn, nrows):
    src = table(f"| id | v | d = {fn}(nope) |", [[f"r_{i}", "1", ""] for i in range(nrows)])
    assert values(impl, src, "d") == [["#REF!(nope)"]] * nrows


@IMPLS
@pytest.mark.parametrize("fn", ["prior", "delta", "cumulative"])
def test_row_relative_over_a_column_on_a_cycle_is_cycle_in_every_row(impl, fn):
    src = table(
        f"| id | v | a = b | b = a | d = {fn}(a) |",
        [["r_1", "1", "", "", ""], ["r_2", "3", "", "", ""]],
    )
    assert values(impl, src, "d") == [[CYCLE], [CYCLE]]


# --- #133: a self-reference through a row-relative call is a cycle ----------


@IMPLS
@pytest.mark.parametrize("fn", ["prior", "delta", "cumulative"])
def test_a_row_relative_column_naming_itself_is_a_cycle(impl, fn):
    src = table(f"| id | v | d = {fn}(d) |", [["r_1", "1", ""], ["r_2", "3", ""]])
    assert values(impl, src, "d") == [[CYCLE], [CYCLE]]


@IMPLS
@pytest.mark.parametrize("fn", ["prior", "delta", "cumulative"])
def test_a_cycle_through_a_row_relative_call_and_another_column(impl, fn):
    src = table(
        f"| id | v | x = {fn}(y) | y = x + v |",
        [["r_1", "1", "", ""], ["r_2", "3", "", ""]],
    )
    assert values(impl, src, "x", "y") == [[CYCLE, CYCLE], [CYCLE, CYCLE]]


@IMPLS
def test_a_cycle_through_a_row_relative_call_and_a_group_aggregate(impl):
    src = table(
        "| id | g | v | p = prior(s) | s = sum(p where g = @g) |",
        [["r_1", "x", "1", "", ""], ["r_2", "x", "2", "", ""]],
    )
    assert values(impl, src, "p", "s") == [[CYCLE, CYCLE], [CYCLE, CYCLE]]


# --- #134: the source is read after it is evaluated, wherever it stands ------


# Each is run with the dependent column's name sorting before its source's and
# after it, and with the source written later in the header and earlier, so
# no visiting order an implementation might happen to use can stand in for
# the dependency.
NAMES = pytest.mark.parametrize(
    "dep, src", [("p", "c"), ("c", "p")], ids=["dep-after", "dep-first"]
)
LATER = pytest.mark.parametrize("later", [True, False], ids=["source-later", "source-earlier"])


def _header(dep_cell, src_cell, later):
    return f"{dep_cell} | {src_cell}" if later else f"{src_cell} | {dep_cell}"


@IMPLS
@NAMES
@LATER
@pytest.mark.parametrize(
    "fn, want",
    [("prior", ["", 3.0]), ("delta", ["", 0.0]), ("cumulative", [3.0, 6.0])],
)
def test_row_relative_over_a_group_aggregate(impl, fn, want, dep, src, later):
    cells = _header(f"{dep} = {fn}({src})", f"{src} = sum(a where g = @g)", later)
    text = table(
        f"| id | g | a | {cells} |",
        [["r_1", "x", "1", "", ""], ["r_2", "x", "2", "", ""]],
    )
    assert [r[0] for r in values(impl, text, dep)] == want


@IMPLS
@NAMES
@LATER
@pytest.mark.parametrize(
    "fn, want",
    [("prior", ["", 1.0, 3.0]), ("delta", ["", 2.0, 3.0]), ("cumulative", [1.0, 4.0, 10.0])],
)
def test_row_relative_over_another_row_relative_column(impl, fn, want, dep, src, later):
    cells = _header(f"{dep} = {fn}({src})", f"{src} = cumulative(v)", later)
    text = table(
        f"| id | v | {cells} |",
        [["r_1", "1", "", ""], ["r_2", "2", "", ""], ["r_3", "3", "", ""]],
    )
    assert [r[0] for r in values(impl, text, dep)] == want


# --- #135: a group aggregate over a column whose first row is blank ----------


@IMPLS
@pytest.mark.parametrize("dep, src", [("s", "p"), ("b", "p")], ids=["dep-after", "dep-first"])
@LATER
@pytest.mark.parametrize("fn, want", [("sum", 3.0), ("count", 3), ("max", 2.0)])
def test_group_aggregate_over_a_prior_column(impl, fn, want, dep, src, later):
    cells = _header(f"{dep} = {fn}({src} where g = @g)", f"{src} = prior(v)", later)
    text = table(
        f"| id | g | v | {cells} |",
        [["r_1", "x", "1", "", ""], ["r_2", "x", "2", "", ""], ["r_3", "x", "4", "", ""]],
    )
    assert values(impl, text, src, dep) == [["", want], [1.0, want], [2.0, want]]


# --- an ordinary formula waits for the row-relative or group column it names --


@IMPLS
@NAMES
@LATER
def test_ordinary_formula_over_a_row_relative_column(impl, dep, src, later):
    cells = _header(f"{dep} = {src} * 2", f"{src} = cumulative(v)", later)
    text = table(
        f"| id | v | {cells} |",
        [["r_1", "1", "", ""], ["r_2", "2", "", ""], ["r_3", "3", "", ""]],
    )
    assert [r[0] for r in values(impl, text, dep)] == [2.0, 6.0, 12.0]


@IMPLS
@NAMES
@LATER
def test_ordinary_formula_over_a_group_aggregate(impl, dep, src, later):
    cells = _header(f"{dep} = {src} * 2", f"{src} = sum(a where g = @g)", later)
    text = table(
        f"| id | g | a | {cells} |",
        [["r_1", "x", "1", "", ""], ["r_2", "x", "2", "", ""], ["r_3", "y", "4", "", ""]],
    )
    assert [r[0] for r in values(impl, text, dep)] == [6.0, 6.0, 8.0]


# --- §4.2 rule 9: the order of the header is not an input to any value -------


@IMPLS
def test_header_order_is_not_an_input(impl):
    cells = [
        "c = sum(a where g = @g)",
        "p = prior(c)",
        "q = cumulative(b)",
        "p2 = delta(q)",
        "b = a / 100000",
        "t = q + c",
    ]
    rows = [["r_1", "x", "1"], ["r_2", "x", "2"], ["r_3", "y", "4"]]
    names = ["c", "p", "q", "p2", "b", "t"]
    seen = set()
    for perm in itertools.permutations(cells):
        src = table(
            "| id | g | a | " + " | ".join(perm) + " |",
            [r + [""] * len(perm) for r in rows],
        )
        seen.add(repr(values(impl, src, *names)))
    b = [1 / 100000, 2 / 100000, 4 / 100000]
    q = [b[0], b[0] + b[1], b[0] + b[1] + b[2]]
    c = [3.0, 3.0, 4.0]
    want = [
        [c[0], "", q[0], "", b[0], q[0] + c[0]],
        [c[1], c[0], q[1], q[1] - q[0], b[1], q[1] + c[1]],
        [c[2], c[1], q[2], q[2] - q[1], b[2], q[2] + c[2]],
    ]
    assert seen == {repr(want)}
