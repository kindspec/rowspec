# Why this case exists

`eq-rhs = string / literal`. There is no `ident` alternative — that is §9.24 —
so the `3` in `qty = 3` is the number three even though this table has a column
literally named `3` holding `99`.

The fixture is arranged the way `eval/bare-numeric-position-decides` is: the
column named `3` is **actually present**, which is the only arrangement that can
tell the rule from the alternative §4.2 rule 7 rejects — "resolve a bare numeric
token to the column if such a column exists, and to a literal otherwise". Under
that alternative `qty = 3` would compare `3` against `99` and `s` would be `0`.

Rule 7's argument is the one that decides it: "it makes the grammar a function
of the table it is parsing ... A grammar that cannot be read without the header
is not a grammar." And rule 10 cites rule 7 by name when it fixes the spelling
rule on the same ground.
