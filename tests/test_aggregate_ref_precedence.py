# SPDX-License-Identifier: Apache-2.0 OR MIT
"""SPEC.md §8: an aggregate whose operands hold several different `#REF!`
values carries one chosen by shape -- cycle, name, `/0`, empty, overflow --
then by the name that sorts first, never by row position (#115).

Every scenario runs with its rows in both orders, because §6 says shuffling
the lines changes no value. Unit tests of the two implementations, not
conformance cases: the cases for this rule come from an author who has not
read `reference/`.
"""

import importlib

import pytest

IMPLS = pytest.mark.parametrize("impl", ["rowspec.table", "rowspec_alt.table"])
BIG = "1" + "0" * 400  # beyond binary64


def both_orders(impl, header, align, rows, decls):
    out = []
    for body in (rows, rows[::-1]):
        src = f"{header}\n{align}\n" + "".join(f"{r}\n" for r in body) + "\nkey := id\n" + decls
        out.append(importlib.import_module(impl).evaluate(src))
    return out


@IMPLS
@pytest.mark.parametrize(
    "rows, want",
    [
        ([f"| r_0 | {BIG} | 1 |  |", "| r_1 | 1 | 0 |  |"], "#REF!(/0)"),
        (["| r_0 | x | 1 |  |", "| r_1 | 1 | 0 |  |"], "#REF!(a)"),
        (["| r_0 | x | 1 |  |", f"| r_1 | {BIG} | 1 |  |"], "#REF!(a)"),
    ],
    ids=["div0-over-overflow", "name-over-div0", "name-over-overflow"],
)
def test_a_computed_column_holding_two_shapes(impl, rows, want):
    for _, aggs in both_orders(
        impl,
        "| id | a | z | c = a / z |",
        "| -- | -: | -: | -: |",
        rows,
        "s := sum(c)\nv := avg(c)\nmn := min(c)\nmx := max(c)\nn := count(c)\n",
    ):
        assert aggs == {"s": want, "v": want, "mn": want, "mx": want, "n": want}


@IMPLS
def test_a_value_that_will_not_coerce_outranks_a_stored_overflow(impl):
    for _, aggs in both_orders(
        impl,
        "| id | a |",
        "| -- | -: |",
        [f"| r_0 | {BIG} |", "| r_1 | x |"],
        "s := sum(a)\nv := avg(a)\nmn := min(a)\nmx := max(a)\nn := count(a)\n",
    ):
        # `count` never coerces, so neither cell is an error to it (§7).
        assert aggs == {
            "s": "#REF!(a)",
            "v": "#REF!(a)",
            "mn": "#REF!(a)",
            "mx": "#REF!(a)",
            "n": 2,
        }


@IMPLS
def test_two_names_give_the_one_that_sorts_first(impl):
    """`c = y + x` is `#REF!(y)` in one row and `#REF!(x)` in the other."""
    for _, aggs in both_orders(
        impl,
        "| id | x | y | c = y + x |",
        "| -- | -: | -: | -: |",
        ["| r_0 | 1 |  |  |", "| r_1 |  | 1 |  |"],
        "s := sum(c)\n",
    ):
        assert aggs == {"s": "#REF!(x)"}


@IMPLS
def test_empty_outranks_overflow(impl):
    """`e` is `#REF!(empty)` in group A, whose `a` is all blank, and
    `#REF!(overflow)` in group B."""
    for _, aggs in both_orders(
        impl,
        "| id | g | a | e = min(a where g = @g) |",
        "| -- | -- | -: | -: |",
        ["| r_0 | A |  |  |", f"| r_1 | B | {BIG} |  |"],
        "s := sum(e)\n",
    ):
        assert aggs == {"s": "#REF!(empty)"}


@IMPLS
def test_a_per_row_group_aggregate_follows_the_same_ranking(impl):
    for rows, _ in both_orders(
        impl,
        "| id | g | a | z | c = a / z | t = sum(c where g = @g) |",
        "| -- | -- | -: | -: | -: | -: |",
        [f"| r_0 | A | {BIG} | 1 |  |  |", "| r_1 | A | 1 | 0 |  |  |"],
        "",
    ):
        assert [str(r["t"]) for r in rows] == ["#REF!(/0)", "#REF!(/0)"]


@IMPLS
def test_div0_outranks_empty(impl):
    """`f` is `#REF!(empty)` in group A, whose `a` is all blank, and
    `#REF!(/0)` in group B."""
    for _, aggs in both_orders(
        impl,
        '| id | g | a | z | e = min(a where g = @g) | f = if(g = "A", e, 1 / z) |',
        "| -- | -- | -: | -: | -: | -: |",
        ["| r_0 | A |  | 1 |  |  |", "| r_1 | B | 1 | 0 |  |  |"],
        "s := sum(f)\n",
    ):
        assert aggs == {"s": "#REF!(/0)"}


@IMPLS
@pytest.mark.parametrize(
    "name, other, want",
    [
        ("overflow", "a / z", "#REF!(/0)"),
        ("empty", "a / z", "#REF!(/0)"),
        ("cycle", "b + 1", "#REF!(cycle)"),
    ],
)
def test_a_ref_ranks_as_spelled(impl, name, other, want):
    """A broken reference to a column named `overflow`, `empty` or `cycle`
    ranks as that shape, not as a name. Read as a name, the first two would
    outrank `#REF!(/0)`, and `#REF!(b)` would sort before `#REF!(cycle)`."""
    for _, aggs in both_orders(
        impl,
        f'| id | g | {name} | a | b | z | c = if(g = "A", {name} + 1, {other}) |',
        "| -- | -- | -- | -: | -: | -: | -: |",
        ["| r_0 | A | x | 1 | 1 | 1 |  |", "| r_1 | B | 1 | 1 |  | 0 |  |"],
        "s := sum(c)\n",
    ):
        assert aggs == {"s": want}
