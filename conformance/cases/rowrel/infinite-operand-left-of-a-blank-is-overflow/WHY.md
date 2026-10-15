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

This case asserts `p = a + x`. Both operands are errors: `a` is
`#REF!(overflow)` by §8, and a blank `x` named in arithmetic is `#REF!(x)`
(§7: "a blank one is a missing operand in a formula the author wrote naming
it. That is `#REF!`"; §8: `#REF!(name)` carries "the column ... whose value
would not coerce").

§8 decides which one the cell carries: "Which `#REF!` a formula carries, when
more than one applies, is decided by POSITION IN THE FORMULA TEXT: the
leftmost." `a` is leftmost, so `p` is `#REF!(overflow)`.
`rowrel/blank-left-of-an-infinite-operand-is-ref-to-the-blank` is the same
sum written the other way round.
