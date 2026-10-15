# Why this case exists

Column `a` holds 9×10^313 (a `9` and 313 zeros) in the table's one row. It
matches `number` (§4.1.6), so it is a well-formed stored number, and its
binary64 value is infinite. Column `x` is blank.

§8: "A **stored** cell whose decimal spelling is finite but whose binary64
value is already infinite is `#REF!(overflow)` wherever it is used as an
operand". §4.2 rule 2: "Every operand is converted to a binary64 double", and
"An operation whose IEEE result is an infinity does not store one." §4.2 rule
2 also says "`NaN` cannot arise", and §8 lists five `#REF!` shapes of which
"none of them is ever a number".

The file holds several columns, one asserted per case, sharing these bytes.

This case asserts `f = if(a > 0, 1, 2)`. §4.2 rule 10: "`<`, `<=`, `>`, `>=`
are **numeric, always**. Both operands are converted as §4.2 rule 2 converts
them, and an operand that is not a number — blank, text, or an error — makes
the whole `cond` that error, by §8". The left operand is `#REF!(overflow)`,
so `f` is `#REF!(overflow)`, not the branch `1` that `inf > 0` would select.
