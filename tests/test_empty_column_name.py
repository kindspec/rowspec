# SPDX-License-Identifier: Apache-2.0 OR MIT
"""An empty column name is `bad-identifier` (§4.1.9, §9.16).

`ident = 1*( LETTER / MARK / NUM / "_" )`: one or more. A header cell that is
empty or holds only space and tab trims to `''`, which is not an `ident`, and
neither is the empty name to the left of a computed cell's `=`. Two empty
names in one header are `bad-identifier` too, not only `duplicate-column`.

Unit tests of the two implementations, not conformance cases: the cases for
this rule come from an author who has not read `reference/`.
"""

import importlib

import pytest

IMPLS = pytest.mark.parametrize("impl", ["rowspec.table", "rowspec_alt.table"])
ENTRY = pytest.mark.parametrize("entry", ["parse", "evaluate"])

HEADERS = {
    "empty": "| id |  |\n| -- | -: |\n| r_1 | 5 |\n",
    "no-padding": "| id ||\n| -- | -: |\n| r_1 | 5 |\n",
    "tab-only": "| id | \t |\n| -- | -: |\n| r_1 | 5 |\n",
    "computed": "| id |  = 1 |\n| -- | -: |\n| r_1 |  |\n",
    "computed-tab": "| id | \t= 1 |\n| -- | -: |\n| r_1 |  |\n",
    "first-column": "|  | id |\n| -: | -- |\n| 5 | r_1 |\n",
    "keyed": "| id |  |\n| -- | -: |\n| r_1 | 5 |\n\nkey := id\n",
}


@IMPLS
@ENTRY
@pytest.mark.parametrize("src", list(HEADERS.values()), ids=list(HEADERS))
def test_an_empty_column_name_is_a_bad_identifier(impl, entry, src):
    table = importlib.import_module(impl)
    with pytest.raises(table.Malformed) as e:
        getattr(table, entry)(src)
    assert e.value.refusal == "bad-identifier"


@IMPLS
def test_two_empty_column_names_may_be_reported_either_way(impl):
    # §9.2 and §9.16 both apply; §9's note admits either identifier.
    table = importlib.import_module(impl)
    with pytest.raises(table.Malformed) as e:
        table.evaluate("| id |  |  |\n| -- | -: | -: |\n| r_1 | 5 | 6 |\n")
    assert e.value.refusal in ("bad-identifier", "duplicate-column")


@IMPLS
def test_a_one_character_column_name_is_still_accepted(impl):
    rows, _ = importlib.import_module(impl).evaluate("| id | _ |\n| -- | -: |\n| r_1 | 5 |\n")
    assert str(rows[0]["_"]) == "5"
