# Why this case exists

Ordered by `n`, `a` holds the text `x`, then `1`, then `2`. This case
asserts `prior(a)` in the second row, whose preceding row holds `x`.

§7: `prior(c)` is "that column's value in the preceding row, blank included";
blank is the only non-number it names. A computed column holds a number or an
error: §4.2 rule 10 says "the format still has exactly two kinds of value — a
number and an error (§8)", and §4.1.6 makes a cell that does not match
`number` "text — `#REF!` when used as an arithmetic or aggregate operand
(§8)". §8: "A value that will not coerce to a number is `#REF!`, not a guess",
and `#REF!(name)` carries "the column ... whose value would not coerce".

So `p` is `#REF!(a)`, not the text `x`.
`rowrel/prior-over-a-number-after-a-text-cell` asserts the third row.
