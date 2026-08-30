# Why this case exists

§4.2 rule 9: "**A cycle evaluates to `#REF!(cycle)`**, in every column on the
cycle and in every column whose formula depends, directly or transitively, on
one. `| x = y | y = x |` and `| b = b + a |` are **accepted files**, not
refusals."

§8: "There are exactly three `#REF!` shapes, and an implementation emits no
fourth." `#REF!(cycle)` is one of them, and it is not interchangeable with
`#REF!(name)`: emitting `#REF!(b)` for a cycle in `b` is the *name* shape, which
§8 reserves for "the column that could not be resolved or whose value would not
coerce", and a reader cannot tell it apart from a broken reference to a column
actually named `b`.

`parse/self-referential-column` and `parse/mutually-recursive-columns` already
assert that these files are accepted and that the evaluator terminates. Neither
asserts the value, which is why the spelling was free to drift.

This one covers the second half of rule 9's sentence — "and in every column
whose formula depends, directly or transitively, on one". `z` is not on the
cycle; it reads `x`, which is.
