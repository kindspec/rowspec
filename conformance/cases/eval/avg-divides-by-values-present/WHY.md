# Why this case exists

SPEC §7, on the blank-skipping rule, names this exact column: "`sum(a)` over
`5`, blank, `3` is `8`; `avg` of the same column is `4`, over the two values
present and not the three rows. `count` still counts the row, because it
counts rows."

`avg` is the one aggregate where skipping has a numerator *and* a denominator,
and the halfway-wrong implementation — skip the blank in the sum, divide by the
row count — passes every case that checks only `sum`. Here that implementation
reports `8 / 3`, not `4`. Asserting `s`, `n` and `av` together in one file pins
the whole triangle: `av` is not `s / n` when a blank is present, and neither
`s` nor `n` moved to make it so.
