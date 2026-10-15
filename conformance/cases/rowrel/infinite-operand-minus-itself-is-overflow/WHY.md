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

This case asserts `d = a - a`. Both operands are the infinite cell, so each is
`#REF!(overflow)` and the difference carries it (§8: errors propagate). The
wrong answers this rules out are the host's `inf - inf`, which is `NaN`, and
`0` from subtracting the exact decimal values.
