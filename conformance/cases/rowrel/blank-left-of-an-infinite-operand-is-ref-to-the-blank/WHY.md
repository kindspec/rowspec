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

This case asserts `q = x + a`, the operands of
`rowrel/infinite-operand-left-of-a-blank-is-overflow` swapped. The blank `x`
is `#REF!(x)` and `a` is `#REF!(overflow)`; §8's leftmost rule ("Which
`#REF!` a formula carries, when more than one applies, is decided by POSITION
IN THE FORMULA TEXT: the leftmost") selects `x`, so `q` is `#REF!(x)`.

§8 gives the reason the rule is textual: evaluation strategy is free (§4.2
rule 9), so a reader that let the overflow check run first, or before the
blank check, would otherwise print a different error for the same bytes.
Together the two cases fail any fixed precedence between the two kinds of
error.
