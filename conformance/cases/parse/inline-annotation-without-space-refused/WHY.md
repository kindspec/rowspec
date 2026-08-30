# Why this case exists

SPEC.md §4.1.10: "An inline annotation is `WSP` followed by `#` to end of line,
on a **declaration line only**; `g := sum(v)# note` has no whitespace before the
`#` and is a malformed declaration."

The grammar agrees: `declaration = *WSP ident *WSP ":=" *WSP rhs [ 1*WSP "#"
*char ] eol` -- the annotation is preceded by `1*WSP`, one or more, not zero.

This is the spec's own example, verbatim. `rowspec.table` refuses it;
`rowspec_alt.table` accepts it. I judge the alternative implementation at fault.
