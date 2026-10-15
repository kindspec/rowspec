# Why this case exists

Ordered by `n`, `a` holds a single U+00A0 NO-BREAK SPACE, then `1`, then
`2`. §4.1.4: "A cell's value is its text with leading and trailing `WSP`
removed, and nothing else removed", and §4.1 defines `WSP` as "ASCII
space U+0020 and horizontal tab U+0009, never the Unicode `White_Space`
property". So the cell is the one-character text U+00A0, not blank.

§7: `prior(c)` is "that column's value in the preceding row, blank included";
blank is the only non-number it names. A computed column holds a number or an
error: §4.2 rule 10 says "the format still has exactly two kinds of value — a
number and an error (§8)", and §4.1.6 makes a cell that does not match
`number` "text — `#REF!` when used as an arithmetic or aggregate operand
(§8)". §8: "A value that will not coerce to a number is `#REF!`, not a guess",
and `#REF!(name)` carries "the column ... whose value would not coerce".

So `prior(a)` in the second row is `#REF!(a)`. A reader that trims U+00A0
sees a blank and answers blank, which §7 gives only for a blank cell.
