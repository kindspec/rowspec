# Why this case exists

Two `t` cells hold a U+000C FORM FEED between other characters.

§4.1: "`char` is any scalar value other than `CR` or `LF`", and
`eol = LF / CRLF ; a lone CR is refused (§3)`. A line ends at LF or CRLF
and nowhere else. U+000C FORM FEED is a `char`, not an `eol`.

So the file has three data rows, each one table line, and `count(t)` is `3`
and `sum(q)` is `7`. A reader that splits lines with its host language's
line-boundary rule (Python's `str.splitlines`, for one) ends a line at the
U+000C FORM FEED, is left with table lines lacking their closing `|`, and refuses
the file (§9.18).
