# Why this case exists

Column `a` holds 10^400 (a `1` and 400 zeros) and `1`. The first matches
`number` (§4.1.6) and its binary64 value is +infinity.

§7: of the five aggregates, "`count` counts rows and never coerces"; "The
other four coerce". So `min` and `max` use each cell as an operand, and §8
says "A **stored** cell whose decimal spelling is finite but whose binary64
value is already infinite is `#REF!(overflow)` wherever it is used as an
operand". §8 again: "An aggregate over any column containing a `#REF!` is
itself `#REF!` — **it must not sum the values it can read**", and "An
aggregate poisoned by a `#REF!` among its operands carries THAT error,
unchanged." Both are `#REF!(overflow)`.

The other cell is finite and no cell is blank or text, so `#REF!(overflow)`
is the only error among the operands.

§7 says `min` and `max` "need no such rule" as the exact-sum one, because
binary64 comparison is exact; that is about order-independence, not about
which operands are valid. A reader that compares the host's infinities gets
one of the two aggregates wrong in a way that looks right: with a positive
infinity `max` is the infinity and `min` is the finite cell, and with a
negative one the reverse. Asserting both, in both signs, fails a reader that
saturates and a reader that skips the bad cell.
