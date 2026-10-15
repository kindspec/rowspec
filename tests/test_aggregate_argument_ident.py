# SPDX-License-Identifier: Apache-2.0 OR MIT
"""An aggregate's argument is an `ident`, or the declaration is malformed (§4.1).

`arg = ident [ 1*WSP "where" 1*WSP predicate ]`, and `ident` admits letters,
marks, digits and `_` only. A control or `Cf` character in the argument
leaves a line `declaration` does not generate, which §4.1.11 and §9.12 refuse
as `malformed-declaration`. It is not a reference to a missing column, which
is what `#REF!(<argument>)` would report.

Unit tests of the two implementations, not conformance cases: the cases for
this rule come from an author who has not read `reference/`.
"""

import importlib

import pytest

IMPLS = pytest.mark.parametrize("impl", ["rowspec.table", "rowspec_alt.table"])

HEAD = "| id | n | c |\n| -- | -: | -- |\n| r_1 | 1 | x |\n| r_2 | 2 | y |\n\nkey := id\n"

ARGS = {
    "nul-before": "\x00n",
    "soh-before": "\x01n",
    "zwsp-before": "\u200bn",
    "zwsp-after": "n\u200b",
    "bom-inside": "n\ufeffn",
    "del-after": "n\x7f",
}


@IMPLS
@pytest.mark.parametrize("arg", list(ARGS.values()), ids=list(ARGS))
def test_a_non_ident_aggregate_argument_is_a_malformed_declaration(impl, arg):
    table = importlib.import_module(impl)
    with pytest.raises(table.Malformed) as e:
        table.evaluate(HEAD + f"t := sum({arg})\n")
    assert e.value.refusal == "malformed-declaration"


@IMPLS
@pytest.mark.parametrize("arg", list(ARGS.values()), ids=list(ARGS))
def test_a_non_ident_aggregate_argument_before_where_is_a_malformed_declaration(impl, arg):
    table = importlib.import_module(impl)
    with pytest.raises(table.Malformed) as e:
        table.evaluate(HEAD + f't := sum({arg} where c = "x")\n')
    assert e.value.refusal == "malformed-declaration"


@IMPLS
@pytest.mark.parametrize("arg", ["", " ", "\t"], ids=["empty", "space", "tab"])
def test_an_empty_aggregate_argument_is_a_malformed_declaration(impl, arg):
    table = importlib.import_module(impl)
    with pytest.raises(table.Malformed) as e:
        table.evaluate(HEAD + f"t := sum({arg})\n")
    assert e.value.refusal == "malformed-declaration"


@IMPLS
def test_an_ident_aggregate_argument_is_still_accepted(impl):
    _, aggs = importlib.import_module(impl).evaluate(
        HEAD + 't := sum(n)\nu := sum(n where c = "x")\n'
    )
    assert (str(aggs["t"]), str(aggs["u"])) == ("3.0", "1.0")
