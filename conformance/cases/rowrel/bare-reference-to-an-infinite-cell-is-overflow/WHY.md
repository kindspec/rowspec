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

This case asserts `c = a`, a formula that is one `primary` and no operator.
The value of `c` is its formula's one operand, converted to binary64 as §4.2
rule 2 converts every operand, and that is the stored cell "used as an
operand" in §8's sentence. A computed value is a number or an error (§4.2
rule 10: "exactly two kinds of value"), a number here is binary64, and the
infinite binary64 value is not one the format stores. The only answer §8
leaves is `#REF!(overflow)`.

The case exists because an implementation that checks for overflow only after
an operator has run never inspects this path: there is no operation, so a
copy of the operand reaches the cell as `inf`.
