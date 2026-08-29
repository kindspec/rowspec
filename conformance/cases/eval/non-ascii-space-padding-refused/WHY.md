# Why this case exists, and why it currently FAILS

Three cells carry a value surrounded by a NON-ASCII space: U+00A0 NO-BREAK
SPACE, U+202F NARROW NO-BREAK SPACE, U+2007 FIGURE SPACE. Each is in *padding*
position, not between digits.

SPEC.md §8: "A value that will not coerce to a number is `#REF!`, not a guess:
thousands separators, parenthesised negatives, and non-ASCII spaces are refused
rather than interpreted."

Discarding a non-ASCII space so the rest of the cell coerces IS interpreting it.
The sentence names three cell-content patterns that a lenient reader would
interpret away and forbids all three; it does not carve out padding position.
`(500)` and `1,500` would also coerce if you interpreted the offending
character.

§9 breaks the tie for anyone who reads "padding is decoration" the other way:
"Reject when degrading could yield a plausible VALUE; preserve and warn when it
could only lose DECORATION." Degrading these three cells yields 20, 5 and 3 --
plausible values -- and a grand total of 253.00 that is indistinguishable from
an honest one. And §4: "A reader that cannot recognise a construct MUST refuse
it, and MUST NOT degrade a failed recognition into a different successful one."

A conforming WRITER never emits non-ASCII padding: §10's canonical form is
single ASCII-space delimiters. So a non-ASCII space in padding position only
ever arrives by paste from a locale-aware spreadsheet or a web page -- which is
exactly the case where U+00A0 and U+202F are a THOUSANDS SEPARATOR, the first
item in §8's own list.

## Resolution

When this case was written the reference trimmed U+00A0/U+202F/U+2007 before
coercion and reported grand = 253.0, so the case FAILED and the
`strip-only-ascii-spaces` mutant SATISFIED it -- the mutant was the
spec-conformant behaviour and the gate entry was aimed backwards. The
implementation was corrected during the same pass and the case now passes.

Keep it: it is the only thing in the tree that distinguishes "padding is
decoration" from "a pasted thousands separator", and the distinction is worth
exactly one plausible-looking wrong total (253.00) per occurrence.
