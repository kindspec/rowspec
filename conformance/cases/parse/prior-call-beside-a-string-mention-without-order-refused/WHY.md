# Why this case exists

The control for `eval/*-inside-a-string-in-a-header-*-is-not-a-call`. The
table is the `where` one from `eval/prior-inside-a-string-in-a-header-where-is-not-a-call`,
with one more column, `p = prior(amt)`: a real `rowrel-call`. No `order` is
declared.

§6: "Without `order`, the table is a SET and the row-relative operators of §7
are refused." §9.9 (`rowrel-without-order`) refuses "a row-relative operator
with no declared order". `p` is one, so the file is refused.

A key is declared and every other cell is well-formed, so no other refusal
applies. Without this case, a reader that never refused a row-relative
operator would pass every accepted case beside it.
