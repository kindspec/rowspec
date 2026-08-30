# Why this case exists, and the contradiction it sits on

**SPEC.md §4.1 currently contradicts itself about this file, in two adjacent
paragraphs.**

Rule 9: "`-` and `.` were admitted by an earlier draft and are not: the formula
language uses `-` as subtraction, so a column named `a-b` would be well-formed
and permanently unreferenceable, and two readers would silently total different
columns."

Rule 9a: "Column names, aggregate names, the argument of `key` and `order`, and
the values of the key column are `ident`: one or more Unicode letters, marks or
digits, `_`, **`-`, `.`**."

The ABNF sides with rule 9: `ident = 1*( LETTER / MARK / NUM / "_" )`. Rule 9a
appears to be the pre-amendment text, left behind when rule 9 was inserted
rather than replaced — its heading, "Identifiers, continued", is not a form used
anywhere else in §4.1.

This case asserts the ABNF's reading, which is two statements out of three and
the one labelled normative. **The implementations are split exactly along the
contradiction**: `rowspec.table` refuses `a-b`, `a.b`, a key value `r-01` and an
aggregate named `a-b`; `rowspec_alt.table` accepts all four. Neither is wrong
against the document as it stands, which is the problem.

If rule 9a is the intended rule instead, retire this case with a note and the
ABNF needs `-` and `.` restored. Either way one of the three statements must
go.
