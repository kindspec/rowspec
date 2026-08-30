# Why this case exists

§4.2 rule 2: "**Division by zero evaluates to `#REF!(/0)`** (§8). It is an error
value and propagates like any other: the row's cell is `#REF!(/0)` and every
aggregate over that column is `#REF!` too."

The spelling is load-bearing, not cosmetic. §8: "There are exactly three
`#REF!` shapes, and an implementation emits no fourth." `rowspec_alt` emits
`#REF!(division by zero)`, which is a fourth shape — and one whose contents are
prose rather than a name, so a tool that parses the value cannot tell it from a
reference to a column with a space in it, which §4.1.9 forbids anyway.

`count` is asserted alongside `sum` because §7's `count` carve-out is scoped to
values that merely fail to parse: a `#REF!` *actually present in the column* —
which `#REF!(/0)` is — still poisons it.
