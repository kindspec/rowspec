# Why this case exists

The write side of §4.2 rule 10's guard. `r_01`'s `qty` goes from `4` to `0`
through the structure, the row's `avg` moves from `5` to the guard's `0`, and
`s` falls from `10` to `5`.

§4.2 rule 2 is explicit that this must not be a refusal: division by zero "is
*not a refusal*, because the divisor is data: a file valid today would become
refused when one cell is edited to `0`, and a validity that turns on a cell's
value belongs to §8's error model rather than to §9's list of things about a
file's shape."

So a `set_cell` that validates by re-parsing and then rejects — or one that
evaluates eagerly and returns `#REF!(/0)` for `s` — fails here for two different
reasons, and the guard the author wrote is what makes `5` the answer rather than
either.
