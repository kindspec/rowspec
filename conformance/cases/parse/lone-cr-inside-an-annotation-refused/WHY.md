# Why this case exists

An annotation line holds a `CR` between `note` and `more`, with no `LF`
after it.

§3: "A lone `CR` is **refused**: it makes two rows share one git line".
§4.1: "`char` is any scalar value other than `CR` or `LF`", and
`eol = LF / CRLF ; a lone CR is refused (§3)`. A line ends at LF or CRLF
and nowhere else. Neither §3 nor §9.15 (`lone-cr`) makes an exception for
the annotation channel, and `annotation = *WSP "#" *char eol` cannot hold
a `CR`.

The `CR` is not a `char`, so the line does not match `annotation` either and
is none of the line kinds (§9.19, `unclassified-line`). Both are listed.
