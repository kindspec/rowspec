# Why this case exists

§8 now says "There are exactly five `#REF!` shapes", and admits the count had
drifted twice — three while `overflow` was already required, four while
`empty` was. This case is the assertion §8 promises: all five shapes, each
produced by its own defining condition, in one table, as exact strings.

- `#REF!(nope)` — a reference to a name that does not exist, carrying the
  originating name
- `#REF!(/0)` — division by zero (§4.2 rule 2)
- `#REF!(cycle)` — a computed column depending on itself (§4.2 rule 9)
- `#REF!(empty)` — `min` over a column whose every cell is blank (§7)
- `#REF!(overflow)` — a stored cell whose binary64 value is infinite, used as
  an operand (§8)

What a fixture can assert is exact values, so the case pins the set from both
directions the runner can see. If a shape goes missing — an implementation
folds `empty` into blank, or `overflow` into `name`, or spells any of them
differently — one of the five assertions fails on its exact string. If an
implementation invents a sixth shape, it can only do so by emitting it for
some condition, and the five conditions here are precisely the ones §8
enumerates, so the sixth shape displaces one of the five and fails that
assertion. A sixth shape emitted for a condition outside §8's enumeration is
by construction a condition the spec gives some other value, which is a
different (existing) case's failure.

`ok` is a control: the errors are values in their own columns, not a property
of the file, and a healthy aggregate beside five broken ones is still `5.0`.
