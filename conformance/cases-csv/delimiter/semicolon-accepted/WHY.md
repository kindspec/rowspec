The sidecar's `delimiter` is `;`. The CSV is `a;b`, then `1,2;3`.

§13: "**A fifth optional member, `delimiter`, names the field separator**: a
string of exactly one Unicode scalar value other than `"`, CR or LF.
Anything else is refused: a non-string, an empty string, a longer one, and
those three, which RFC 4180 reserves for quoting and for ending a record, so
a delimiter equal to one of them leaves the record boundaries undefined."

§9.6 (`row-field-count`) refuses "a data row whose field count differs from
the header", and §13 reads record boundaries as RFC 4180's.

Split on `;`, the header and the row are two fields each (`1,2` is one
field), so the file is accepted. Split on the default comma, the header is
one field and the row two, which §9.6 refuses: a reader that ignores
`delimiter` refuses this file.
