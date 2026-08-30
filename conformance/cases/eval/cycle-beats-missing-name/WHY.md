# Why this case exists

§8: "`#REF!(cycle)` takes precedence over `#REF!(name)` when a column is both
on a cycle and names something absent: a cycle is a property of the whole
header, and reporting a missing name would send a reader to add a column that
would not help."

`x` is both: it sits on the cycle `x → y → x` and it names `nope`, which does
not exist. `nope` is deliberately the *leftmost* name in `x`'s formula, so the
leftmost rule — which this same section introduces — cannot be the tiebreaker
here: an implementation that folds cycle detection into ordinary name
resolution and then takes the leftmost failure answers `#REF!(nope)`, which is
the diagnostic §8 calls useless — adding a column named `nope` leaves the
cycle exactly where it was. `sy` checks the column that is on the cycle but
names nothing absent, where the two rules agree.
