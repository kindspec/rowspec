# SPDX-License-Identifier: Apache-2.0 OR MIT
"""SPEC.md §8: a stored cell whose binary64 value is infinite is
`#REF!(overflow)` wherever it is used as an operand, and §4.2 rule 2 stores no
infinity (#107). This is the row-expression path: arithmetic, `if`
comparisons, numeric literals, and the row-relative operators.

Both implementations run every case, so a fix in one cannot leave the two
disagreeing.
"""

import math
import os
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

import rowspec.table as ref  # noqa: E402
import rowspec_alt.table as alt  # noqa: E402

BIG = "9" + "0" * 313  # beyond binary64
OVF = "#REF!(overflow)"

IMPLS = pytest.mark.parametrize("impl", [ref, alt], ids=["reference", "rowspec_alt"])


def column(impl, formula, values):
    rows = "".join(f"| r_{i} | {v} |  |\n" for i, v in enumerate(values))
    src = f"| id | a | b = {formula} |\n| -- | -: | -: |\n{rows}\nkey := id\norder := by(id)\n"
    out, _ = impl.evaluate(src)
    got = [r["b"] for r in out]
    # No path may emit a non-finite number: §4.1.6 cannot spell one.
    assert not any(isinstance(v, float) and not math.isfinite(v) for v in got), got
    return got


@IMPLS
@pytest.mark.parametrize(
    "formula",
    ["a", "-a", "a - a", "a * 0", "a / a", "if(a > 0, 1, 2)", "if(a = 0, 1, 2)", "if(a > a, 1, 2)"],
)
def test_an_infinite_cell_is_overflow_as_an_operand(impl, formula):
    assert column(impl, formula, [BIG]) == [OVF]


@IMPLS
@pytest.mark.parametrize(
    "formula",
    [
        f"{BIG} * 0",
        f"{BIG} - {BIG}",
        f"if(a > 0, {BIG}, 0)",
        f"if(a > {BIG}, 1, 2)",
        f"if(a < -{BIG}, 1, 2)",
        f"if(a = {BIG}, 1, 2)",
        BIG,
        f"-{BIG}",
        f"{BIG}.5",
        f"a + {BIG}",
    ],
    ids=[
        "times-zero",
        "minus-itself",
        "if-branch",
        "order-bound",
        "negated-bound",
        "equality",
        "bare",
        "negated",
        "with-a-fraction",
        "an-operand",
    ],
)
def test_an_infinite_literal_is_overflow(impl, formula):
    """§8: a numeric literal beyond binary64 is `#REF!(overflow)`, like a stored
    cell (#117), and the formula holding it is not refused."""
    assert column(impl, formula, ["5"]) == [OVF]


@IMPLS
@pytest.mark.parametrize(
    "formula, values, want",
    [
        ("delta(a)", [BIG, BIG], [OVF, OVF]),
        ("delta(a)", ["x", BIG], ["#REF!(a)", OVF]),
        ("prior(a)", [BIG, "1", "2"], ["", OVF, 1.0]),
        ("cumulative(a)", [BIG, "-" + BIG, "1"], [OVF, OVF, OVF]),
        ("cumulative(a)", [BIG, ""], [OVF, OVF]),
    ],
    ids=[
        "delta-of-two-infinities",
        "delta-of-an-infinity-after-text",
        "prior-of-an-infinity",
        "cumulative-of-opposite-infinities",
        "cumulative-stays-overflow-past-a-blank",
    ],
)
def test_an_infinite_cell_is_overflow_in_a_row_relative_operator(impl, formula, values, want):
    assert column(impl, formula, values) == want


@IMPLS
def test_count_over_a_column_holding_the_overflow_is_poisoned(impl):
    """§7: `count` is poisoned by a `#REF!` actually present in the column, and
    a computed column over an infinite cell holds one."""
    src = (
        f"| id | a | b = a |\n| -- | -: | -: |\n| r_1 | {BIG} |  |\n| r_2 | 1 |  |\n\n"
        "key := id\nn := count(b)\n"
    )
    _, aggs = impl.evaluate(src)
    assert aggs == {"n": OVF}


def two_columns(impl, formula, a, x):
    src = (
        f"| id | a | x | b = {formula} |\n| -- | -: | -: | -: |\n| r_1 | {a} | {x} |  |\n\n"
        "key := id\n"
    )
    out, _ = impl.evaluate(src)
    return out[0]["b"]


@IMPLS
@pytest.mark.parametrize(
    "formula, want",
    [
        ("a + x", OVF),
        ("x + a", "#REF!(x)"),
        ("if(a > x, 1, 2)", OVF),
        ("if(x > a, 1, 2)", "#REF!(x)"),
        (f"if(x = {BIG}, 1, 2)", OVF),
        (f"if(x > {BIG}, 1, 2)", OVF),
    ],
    ids=["a-plus-x", "x-plus-a", "a-above-x", "x-above-a", "x-equals-big", "x-above-big"],
)
def test_the_leftmost_error_wins_over_an_infinite_operand(impl, formula, want):
    """§8: of two errors, the leftmost in the formula text. `a` is infinite and
    `x` is blank, so each is an error and only position decides between them.
    A literal beyond binary64 is a header error instead (§4.2 rule 10, #117),
    so it outranks a blank `x` wherever it sits."""
    assert two_columns(impl, formula, BIG, "") == want


@IMPLS
@pytest.mark.parametrize(
    "formula",
    [
        f"if(a > 0, 1, {BIG})",
        f"if(a < 0, 1, {BIG})",
        f"if(a > 0, {BIG}, 1)",
        f"if(a > 0, 1, if(a > 0, 2, {BIG}))",
        f"if(a > 0, if(a < 0, {BIG}, 2), 1)",
    ],
    ids=["else-branch", "else-branch-flipped", "then-branch", "nested-else", "nested-then"],
)
def test_an_infinite_literal_is_overflow_in_every_row(impl, formula):
    """§8 by §4.2 rule 10's reasoning: the literal's cause is in the header, so
    it is `#REF!(overflow)` in every row, a row that takes the other branch of
    an `if` included (#117). One row of each sign, so each branch is taken."""
    assert column(impl, formula, ["5", "-5"]) == [OVF, OVF]


@IMPLS
@pytest.mark.parametrize(
    "formula, values, want",
    [
        (f"{BIG} + nope", ["5"], OVF),
        (f"nope + {BIG}", ["5"], "#REF!(nope)"),
        (f"1 / 0 + {BIG}", ["5"], OVF),
        (f"a + {BIG}", [""], OVF),
        (f"if(a > {BIG}, 1, 2)", [""], OVF),
    ],
    ids=[
        "literal-then-name",
        "name-then-literal",
        "div0-then-literal",
        "blank-then-literal",
        "blank-bound",
    ],
)
def test_an_infinite_literal_is_a_header_error(impl, formula, values, want):
    """Like an unresolved name (§4.2 rule 10), it outranks any error that comes
    from the data, and of two header errors the leftmost wins (§8)."""
    assert column(impl, formula, values) == [want]
