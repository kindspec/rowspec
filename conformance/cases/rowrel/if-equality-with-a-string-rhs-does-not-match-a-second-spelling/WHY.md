# Why this pair exists

§4.2 rule 10: "`=` and `<>` compare **text or numbers, and the right-hand
side's spelling decides which**. A `string` right-hand side compares text under
rule 6's treatment, unchanged — trimmed, unescaped, NFC. A `literal` right-hand
side compares numbers. So `if(qty = "3", …)` matches a cell holding `3` and not
one holding `3.0`, while `if(qty = 3, …)` matches both."

**The pair is the test.** Either file alone passes under an implementation that
picked one reading and applied it to both spellings: a text-only reader gets `1`
here and `1` on the literal file where the answer is `2`; a numeric-only reader
gets `2` on both. Only the two files on *identical data* separate them, and the
data is chosen so the two readings disagree — `3` and `3.0` are equal as numbers
and unequal as text, which is precisely the split §4.1.6 refused a second
spelling of a number to avoid.

The `<>` half of the same sentence is
`eval/if-not-equal-with-a-string-rhs-compares-text` and
`eval/if-not-equal-with-a-literal-rhs-compares-numbers`, and the single-cell
form that names the disagreeing row is
`rowrel/if-equality-with-a-string-rhs-does-not-match-a-second-spelling`.

The alignment column for `qty` is `---` rather than `--:` deliberately: §4.1.5's
alignment is decoration and must not be an input to how a cell is read.
