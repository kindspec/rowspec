# Why this case exists

§8: "A **stored** cell whose decimal spelling is finite but whose binary64
value is already infinite is `#REF!(overflow)` wherever it is used as an
operand, for the same reason: §9.10 refuses the *spellings* `inf` and `nan`,
and a four-hundred-digit cell is neither."

The cell is four hundred nines — a well-formed `number` under §4.1.6, so the
file is accepted — whose binary64 conversion is already an infinity before
any operator runs. Both operand routes are asserted, because they are
different code paths and an implementation can easily guard one and not the
other:

- `sx` uses the cell as an operand of `expr` arithmetic (`big + 1`). Rule 2's
  overflow check watches the *result* of an operation; here the infinity
  walks in as an input, so a check placed only after each operator misses it
  — `inf + 1` is `inf`, and the "operation whose IEEE result is an infinity"
  test happens to fire, but `if(big > 0, 1, 0)` or a bare `x = big` would
  not run any operator at all. The conversion itself is where the check
  belongs, and `sx` fails an implementation that converts unchecked.
- `sb` uses the cell as an operand of an aggregate directly, with no computed
  column in the path.

Neither may be `inf`, and neither may be a number: a conversion that
saturates to `1.7976931348623157e308` instead of overflowing produces a
plausible enormous total, which is §1's failure with extra digits.
