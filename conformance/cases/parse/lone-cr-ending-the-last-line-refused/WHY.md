# Why this case exists

The file's last line is `s := sum(q)` followed by a `CR` and no `LF`.

§3: "A lone `CR` is **refused**". §4.1: "`char` is any scalar value other than `CR` or `LF`", and
`eol = LF / CRLF ; a lone CR is refused (§3)`. A line ends at LF or CRLF
and nowhere else. §4.1.1: "The terminator on the
file's last line is optional", but a `CR` with no `LF` after it is not a
terminator: `eol` is `LF` or `CRLF`. §9.15 (`lone-cr`) applies.

The `CR` is not a `char`, so the line also does not match `declaration`,
and it contains `:=` (§9.12, `malformed-declaration`); it is then none of
the line kinds (§9.19, `unclassified-line`). §9: "where several apply, the
case names each of them, and reporting any one passes." A reader that
strips a trailing `CR` before classifying lines accepts the file.
