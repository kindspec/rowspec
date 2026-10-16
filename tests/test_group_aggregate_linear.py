# SPDX-License-Identifier: Apache-2.0 OR MIT
"""A per-row group aggregate is computed once per distinct group, not once per
row (#195). Scanning every row for every row made `sum(v where k = @k)`
quadratic in the row count: about 31 s for `rowspec check` at 10,000 rows.

The count of aggregations is the measure rather than a wall-clock time, which
would be a flaky check. Unit tests of the reference, not conformance cases: the
cases come from an author who has not read `reference/`.
"""

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

from rowspec import table  # noqa: E402

N, CATS = 700, 7


def src(formula):
    rows = "".join(f"| r_{i} | c{i % CATS} | {i % 2} | {i} |  |\n" for i in range(N))
    return f"| id | cat | g | v | t = {formula} |\n| -- | -- | -- | -: | -: |\n{rows}\nkey := id\n"


def counted(monkeypatch):
    calls = []
    real = table._agg

    def agg(fn, vals, what):
        calls.append(len(vals))
        return real(fn, vals, what)

    monkeypatch.setattr(table, "_agg", agg)
    return calls


def test_one_aggregation_per_distinct_group(monkeypatch):
    calls = counted(monkeypatch)
    seq, _ = table.evaluate(src("sum(v where cat = @cat)"))
    assert len(calls) == CATS
    assert sum(calls) == N
    for r in seq:
        k = int(r["cat"][1:])
        assert r["t"] == sum(i for i in range(N) if i % CATS == k)


def test_a_conjunction_with_a_literal_groups_by_both(monkeypatch):
    calls = counted(monkeypatch)
    seq, _ = table.evaluate(src('count(v where cat = @cat and g = "1")'))
    # Every row asks for its own cat with g = "1": one group per cat, each
    # holding that cat's odd rows -- including for a row whose g is "0".
    assert len(calls) == CATS
    for r in seq:
        k = int(r["cat"][1:])
        assert r["t"] == sum(1 for i in range(N) if i % CATS == k and i % 2 == 1)


def test_a_row_whose_group_is_empty(monkeypatch):
    calls = counted(monkeypatch)
    seq, _ = table.evaluate(src('min(v where cat = "none" and g = @g)'))
    assert len(calls) == 2
    assert {r["t"] for r in seq} == {"#REF!(empty)"}
