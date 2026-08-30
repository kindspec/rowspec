# Why this case exists

SPEC.md §4.1.7: "**Dates compare as the integer tuple `(y, m, d)`, never as
strings.** String comparison sorts a hand-typed `2026-2-1` after `2026-03-01`
because `'2' > '0'`; §6's order then drives `cumulative`, so an overdraft check
reads a running balance of `55.0` where the truth is `5.0` -- a plausible
number, not an error."

This is that example, with the spec's own numbers. Under the integer tuple,
`2026-2-1` leads and the first balance is 5.0 (`lo`). Under string comparison
`2026-03-01` leads and `lo` is 50.0, with the same 55.0 total either way -- so
only the running minimum reveals the defect, which is exactly the spec's point
about a plausible number rather than an error.
