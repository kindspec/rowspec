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

This case asserts `delta(a)` in the second row: this row's value is the
infinite cell and the previous row's is `1`. §7: `delta(c)` is "c minus
prior(c)", a subtraction whose left operand is `#REF!(overflow)` by §8, so the
cell is `#REF!(overflow)`. §7 also says "so is a `delta` whose subtraction
leaves range", so the host's `inf - 1 = inf` must not reach the cell either
way.
