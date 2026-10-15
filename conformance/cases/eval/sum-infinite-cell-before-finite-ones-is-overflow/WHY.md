# Why this case exists

Column `a` holds, in file order, 9×10^313 (a `9` and 313 zeros), then
9×10^307 twice. Each is a well-formed `number` under §4.1.6. The first one's
binary64 value is already infinite; the other two are finite.

§8: "A **stored** cell whose decimal spelling is finite but whose binary64
value is already infinite is `#REF!(overflow)` wherever it is used as an
operand." `sum` and `avg` use each cell as an operand (§7: "The other four
coerce"), so one operand is `#REF!(overflow)`. §8 again: "An aggregate over
any column containing a `#REF!` is itself `#REF!`", and "An aggregate
poisoned by a `#REF!` among its operands carries THAT error, unchanged."
Both aggregates are `#REF!(overflow)`.

The row order is the point. §7 defines `sum` and `avg` on the exact
mathematical sum and mean of the multiset, and §6 says shuffling every line
leaves all values unchanged, so the answer cannot depend on whether the
infinite cell comes before or after the finite ones. An exact-summation
routine that receives an infinity first and then more finite values has to
deal with a non-finite input in its state; one that tries to convert that
infinity to an exact rational fails rather than returning a value. The
outcome must still be `#REF!(overflow)`, not a crash, not `inf`, and not a
saturated `1.7976931348623157e308`.

`avg` is asserted beside `sum` because §7 defines it by its own exact-mean
rule rather than as `sum / count`, so an implementation can guard one and
miss the other.
