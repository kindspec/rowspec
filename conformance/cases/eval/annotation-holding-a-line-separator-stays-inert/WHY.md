# Why this case exists

The line after the blank line is an annotation: `# note`, a U+2028 LINE SEPARATOR, then
`| r_9 | 100 |`.

§4.1: "`char` is any scalar value other than `CR` or `LF`", and
`eol = LF / CRLF ; a lone CR is refused (§3)`. A line ends at LF or CRLF
and nowhere else. `annotation = *WSP "#" *char eol`, and U+2028 LINE SEPARATOR is a `char`, so the
whole line is one annotation. §4.1.10: "everything after the `#` is inert,
whatever it looks like".

So `s` is `3` and `n` is `2`. A reader that ends a line at the U+2028 LINE SEPARATOR sees
a table line after the table and refuses the file (§9.19), or gains a row.
