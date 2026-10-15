# SPDX-License-Identifier: Apache-2.0 OR MIT
"""SPEC.md §4.1: `WSP = SP / HTAB`, never the Unicode White_Space property
(#143). U+00A0 or another Unicode space where the grammar allows `WSP`, around
a line, a header cell or a declaration, makes the line match no alternative
of `line` or fail its own production, so the file is refused.

Unit tests of the two implementations, not conformance cases: the cases for
this rule come from an author who has not read `reference/`.
"""

import importlib

import pytest

IMPLS = pytest.mark.parametrize("impl", ["rowspec.table", "rowspec_alt.table"])
SPACES = pytest.mark.parametrize("sp", ["\u00a0", "\u2003", "\u3000"], ids=["nbsp", "em", "ideo"])

H = "| id | a | b = a + 1 |\n| -- | -- | -- |\n"
R = "| r_1 | 1 |  |\n"
G = "| id | a | b = {} |\n| -- | -- | -- |\n" + R + "\nkey := id\n"

# name -> (source with `{}` where the space goes, the refusal)
CASES = {
    "after-closing-pipe": (H + "| r_1 | 1 |  |{}\n\nkey := id\n", "malformed-table-line"),
    "before-leading-pipe": (H + "{}| r_1 | 1 |  |\n\nkey := id\n", "unclassified-line"),
    "line-of-only-the-space": (H + R + "{}\nkey := id\n", "unclassified-line"),
    "before-annotation": (H + R + "\n{}# note\nkey := id\n", "unclassified-line"),
    "around-header-name": (
        "| id | a | {}b{}= a + 1 |\n| -- | -- | -- |\n" + R + "\nkey := id\n",
        "bad-identifier",
    ),
    "around-formula": (
        "| id | a | b ={}a + 1{} |\n| -- | -- | -- |\n" + R + "\nkey := id\n",
        "malformed-formula",
    ),
    "inside-formula": (G.replace("{}", "a{}+ 1"), "malformed-formula"),
    "group-before-and": (G.replace("{}", "sum(a where id = @id{}and a = @a)"), "malformed-formula"),
    "in-declaration": (H + R + "\nkey :={}id\n", "malformed-declaration"),
    "after-declaration": (H + R + "\nkey := id\nt := sum(a){}\n", "malformed-declaration"),
    "before-assign": (H + R + "\nkey := id\nt{}:= sum(a)\n", "malformed-declaration"),
    "in-aggregate-call": (H + R + "\nkey := id\nt := sum({}a)\n", "malformed-declaration"),
    "in-order-call": (H + R + "\nkey := id\norder := by(id{})\n", "malformed-declaration"),
    "before-where-column": (
        H + R + '\nkey := id\nt := sum({}a where id = "r_1")\n',
        "malformed-declaration",
    ),
    "in-where": (
        H + R + '\nkey := id\nt := sum(a where id = "r_1"{}and a = "1")\n',
        "malformed-declaration",
    ),
}


def refusal(impl, src):
    mod = importlib.import_module(impl)
    with pytest.raises(mod.Malformed) as e:
        mod.evaluate(src)
    return e.value.refusal


@IMPLS
@SPACES
@pytest.mark.parametrize("case", list(CASES))
def test_a_unicode_space_is_not_wsp(impl, sp, case):
    src, want = CASES[case]
    assert refusal(impl, src.replace("{}", sp)) == want


@IMPLS
@pytest.mark.parametrize("case", list(CASES))
def test_space_and_tab_are_wsp(impl, case):
    """The same positions with ASCII space and tab are accepted, so the
    refusal above is about the character and not the position."""
    src, _ = CASES[case]
    rows, _ = importlib.import_module(impl).evaluate(src.replace("{}", " \t"))
    assert [r["id"] for r in rows] == ["r_1"]
