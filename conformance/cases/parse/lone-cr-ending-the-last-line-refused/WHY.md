# Why this case exists

The file's last line is `s := sum(q)` followed by a `CR` and no `LF`.

§3: "A lone `CR` is **refused**". §4.1: "`char` is any scalar value other than `CR` or `LF`", and
`eol = LF / CRLF ; a lone CR is refused (§3)`. A line ends at LF or CRLF
and nowhere else. §4.1.1: "The terminator on the
file's last line is optional", but a `CR` with no `LF` after it is not a
terminator: `eol` is `LF` or `CRLF`. §9.15 (`lone-cr`) applies.

The `CR` is not a `char`, so the line also does not match `declaration`,
and it contains `:=` (§9.12, `malformed-declaration`). §9: "where several
apply, the case names each of them, and reporting any one passes." As in the
suite's other cases for a `:=` line that fails `declaration`, §9.19 is not
listed. A reader that strips a trailing `CR` before classifying lines
accepts the file.

## Re-derived at `52be434`

SPEC.md #264 changed §9.15: a lone `CR` in a `.mdtbl` file is decided before any line is classified, and the line holding it is classified as though the `CR` were not there. The reasoning above that lists `lone-cr`, `malformed-declaration` describes this case under the earlier text; the case now asserts `lone-cr`.

§9.15: "`lone-cr`: a lone `CR` (§3). Like §9.14 it is a property of the bytes, decided before any line is classified, so in a `.mdtbl` file a lone `CR` is never also a character of the line holding it: that line is classified as though the `CR` were not there. Without this, every lone `CR` in a `.mdtbl` file would also be §9.12, §9.18 or §9.19, because `char` excludes `CR` and the line holding one matches no alternative of `line`."

§4.1: "eol = LF / CRLF ; a lone CR is refused (§3)"

§4.1.1: "The terminator on the file's last line is optional; its presence or absence is part of the file's bytes, is preserved by `render` and by `canon`, which never adds one, and never changes the parse."

With the `CR` set aside, the last line is `s := sum(q)` with no terminator, which §4.1.1 allows on the last line. It matches `declaration`. The rest of the file is valid: one data row, `key := id` naming a stored column whose value `r_1` is an `ident`. So §9.15 is the only refusal. §9.12 (`malformed-declaration`), listed before, no longer applies, because the `CR` is no longer a character of the line that keeps it from matching.

Re-derived from SPEC.md at rowspec `52be434` alone, by an author who saw no
implementation. SPEC.md sha256
`7e9fb663c7391f4c393c9d9eb8b5c673f4fb22f221c4b29b3119aaf3a36d3884`.
