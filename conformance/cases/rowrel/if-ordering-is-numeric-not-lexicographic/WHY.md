# Why this case exists

§4.2 rule 10: "`<`, `<=`, `>`, `>=` are **numeric, always**. Both operands are
converted as §4.2 rule 2 converts them".

`10 < 9` is false. `"10" < "9"` is true, because `'1'` precedes `'9'`. This is
the one-cell file where a textual ordering implementation produces `1` instead
of `0` with no error anywhere — the cell is a perfectly good number, the formula
is perfectly well-formed, and the only symptom is the answer.

`parse/if-ordering-with-a-string-rhs-refused` catches an implementation that
admits string operands. This one catches an implementation that admits only
numeric-shaped operands and then compares them as strings anyway, which no
refusal can reach.

§4.1.7 records the same bug in the same format from the other end: "String
comparison sorts a hand-typed `2026-2-1` after `2026-03-01` because `'2' > '0'`
... an overdraft check reads a running balance of `55.0` where the truth is
`5.0` — a plausible number, not an error."
