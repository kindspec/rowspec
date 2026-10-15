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

This case asserts `delta(a)` in the third row: this row's value is `2` and the
previous row's is the infinite cell. `delta(c)` is "c minus prior(c)" (§7),
and the right operand `prior(a)` is the infinite cell, `#REF!(overflow)` by
§8. Only one operand is an error, so the cell is `#REF!(overflow)`. A host
`2 - inf` is `-inf`, which the format cannot store.
