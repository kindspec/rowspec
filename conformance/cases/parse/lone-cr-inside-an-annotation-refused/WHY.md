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

## Re-derived at `52be434`

SPEC.md #264 changed §9.15: a lone `CR` in a `.mdtbl` file is decided before any line is classified, and the line holding it is classified as though the `CR` were not there. The reasoning above that lists `lone-cr`, `unclassified-line` describes this case under the earlier text; the case now asserts `lone-cr`.

§9.15: "`lone-cr`: a lone `CR` (§3). Like §9.14 it is a property of the bytes, decided before any line is classified, so in a `.mdtbl` file a lone `CR` is never also a character of the line holding it: that line is classified as though the `CR` were not there. Without this, every lone `CR` in a `.mdtbl` file would also be §9.12, §9.18 or §9.19, because `char` excludes `CR` and the line holding one matches no alternative of `line`."

§4.1.10: "A whole-line annotation is a line whose first non-`WSP` character is `#`, outside the table; everything after the `#` is inert, whatever it looks like"

§4.1.2: "Annotations and blank lines may precede and follow it; they may not appear inside it."

With the `CR` set aside, the line is `# notemore`, a whole-line annotation after the table and its blank line, before the declarations. Nothing else in the file is refused. So §9.15 is the only refusal. §9.19 (`unclassified-line`), listed before, no longer applies.

Re-derived from SPEC.md at rowspec `52be434` alone, by an author who saw no
implementation. SPEC.md sha256
`7e9fb663c7391f4c393c9d9eb8b5c673f4fb22f221c4b29b3119aaf3a36d3884`.
