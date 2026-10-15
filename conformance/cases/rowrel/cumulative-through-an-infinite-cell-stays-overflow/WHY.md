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

This case asserts `cumulative(a)` in the last row. §7: each value of
`cumulative` "is one binary64 addition of the next value to the previous
running total, taken over the **declared order**", and "That addition is an
operation for the purposes of §4.2 rule 2, so a step whose result is an
infinity is `#REF!(overflow)` and propagates from there".

The second step adds the infinite cell, an operand that is `#REF!(overflow)`
by §8, so the running total is `#REF!(overflow)` from the second row. The
third and fourth steps add `2` and `5` to that error, and §8's errors
propagate, so the last row is still `#REF!(overflow)`. The last row is
asserted because it separates a reader that propagates the error from one
that restarts the running total, or skips the bad row, after it.
