# Why this case exists

`eq-rhs = string / signed`, so `signed` reaches the equality operators too and
`if(a = -2, …)` is a **numeric** comparison against negative two.

The file is the negative-number form of
`eval/if-equality-with-a-string-rhs-compares-text` and its literal sibling,
collapsed into one header so the spelling rule and the sign interact in a single
assertion. §4.2 rule 10: "A `string` right-hand side compares text ... A
`literal` right-hand side compares numbers." `-2` and `-2.0` are one number and
two strings, so `sm` is `2` and `st` is `1`.

`st` is the half that catches the tempting shortcut. An implementation that
implements `signed` by *stripping* a leading `-` from the right-hand side and
negating afterwards has to decide what to do when the right-hand side is a
`string`, and the answer is nothing at all — `"-2"` is a string whose first
character happens to be a hyphen, `signed` never sees it, and the comparison is
textual against those exact characters. Strip it there and `st` becomes `2`.

§4.1.6 admits `-2.0` as a `number` and refuses no second spelling of it, which
is what makes the numeric/textual split visible on this data at all.
