# Why this case exists

§4.2 rule 6: "**§4.1.3's `\|` does not reach inside a string literal, and
cannot.** Unescaping happens when the *table line* is split into cells, before
any formula is looked at, so a header cell's formula is already unescaped by the
time this grammar applies." Rule 10 inherits rule 6's treatment verbatim for a
`string` right-hand side — "compares text under rule 6's treatment, unchanged —
trimmed, unescaped, NFC" — so the escaped spelling in a header cell must match a
data cell written the same way.

Rule 6 states the consequence of getting it backwards: "the predicate matches
zero rows and reports `0`". Here it would report `0` for `s`, and the file
contains a second row whose region genuinely does not match, so a reader that
unescapes at the wrong layer cannot land on the right total by accident.

The pipe case matters more than it looks: §4.1.3's [CHOICE] records that
"Ninety-three television channels in one public registry have a pipe in their
own name".
