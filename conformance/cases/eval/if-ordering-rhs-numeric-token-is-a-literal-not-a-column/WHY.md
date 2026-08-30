# Why this case exists

§4.2 rule 7: "**Operand position** — `primary`, and a `comparison`'s
**right-hand** side — tries `literal` first, so a token matching `literal` is a
number."

So the `3` in `qty > 3` is the number three even though this table has a column
literally named `3` holding `99`. Under the alternative rule 7 rejects —
"resolve a bare numeric token to the column if such a column exists, and to a
literal otherwise" — `qty > 3` would compare `5` against `99` and `s` would be
`0`.

The fixture is arranged the way `eval/bare-numeric-position-decides` is: the
column named `3` is **actually present**, which is the only arrangement that can
tell the rule from that alternative. Rule 7's argument is what decides it: "it
makes the grammar a function of the table it is parsing ... A grammar that
cannot be read without the header is not a grammar."

**This case was written when rule 7 did not name this position at all.** Rule 7
said "Two positions exist and each admits exactly one of them" and then listed
them — name positions, and `primary` — and `order-rhs` was in neither list, even
though it is the one position in the format with *both* alternatives
(`order-rhs = signed / ident`). An implementer who trusted the list as
exhaustive had no rule for this token and would take whichever their parser
tried first, and both readings produce a number with no diagnostic. Rule 7 now
names it.

`rowrel/if-comparison-lhs-numeric-token-is-a-column-name` is the same token on
the other side of the same operator, with the opposite answer.
