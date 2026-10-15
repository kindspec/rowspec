# Why this case exists

`c = a + nope` names a column that does not exist. §8: "A reference to a
name that does not exist evaluates to `#REF!(name)`", and §4.2 rule 10:
"**A name that does not resolve is `#REF!(name)` in EVERY row**". So `c` is
`#REF!(nope)` in every row, the first included. `d = delta(c)` names `c`,
which resolves; the unresolved name is inside `c`'s formula, not `d`'s.

§7: "In the first row, which has no preceding row, `delta(c)` is blank
only when `c` is a number, and otherwise carries the error `c` gives
there, a blank included, as it does in every later row."

§7: "Each operand carries the error it originated, so a computed `c`
holding `#REF!(/0)` here makes `delta(c)` `#REF!(/0)`, not a relabelled
`#REF!(c)`." The same holds for a name: `c` originated `#REF!(nope)`.

So `d` in the first row is `#REF!(nope)`, not blank and not `#REF!(c)`.

The row that comes first in the declared order is the second line of the
file. Every row of `c` here gives the same error, so this case does not
catch a reader that takes "first" from file position: either row's `d` is
that error. The number control,
`rowrel/delta-first-row-over-a-computed-number-is-blank`, does.
