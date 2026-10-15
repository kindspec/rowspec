# Why this case exists

Ordered by `n`, column `a` holds `1`, then 9×10^313 (a `9` and 313 zeros),
then `2`, then `5`. The second value matches `number` (§4.1.6) and its
binary64 value is infinite; the others are ordinary.

§8: "A **stored** cell whose decimal spelling is finite but whose binary64
value is already infinite is `#REF!(overflow)` wherever it is used as an
operand". §4.2 rule 2 stores no infinity and says "`NaN` cannot arise".

The order is declared, the order column is numeric with no blank, and a key is
declared, so the file is accepted (§6, §9.9, §9.10, §9.25). Several cases
share these bytes, each asserting one cell. No asserted cell meets an error in
both this row and the previous one, so none depends on which of two errors a
row-relative operator carries.

This case asserts `prior(a)` in the third row, whose preceding row holds the
infinite cell. §7: `prior(c)` is "that column's value in the preceding row".
That value becomes the value of the computed column `p`, which can only be a
number or an error (§4.2 rule 10: "exactly two kinds of value"). A number is
binary64 (§4.2 rule 2), and this one is infinite, which the format never
stores. §8's sentence covers it: the cell is `#REF!(overflow)` wherever it is
used, and here it is the operand that `prior` passes on. So `p` is
`#REF!(overflow)`, not `inf` and not the 314-digit text.
