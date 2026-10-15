The sidecar's `delimiter` is `;`. The CSV is `a,b`, then `1;2,3`.

§13: "**A fifth optional member, `delimiter`, names the field separator**: a
string of exactly one Unicode scalar value other than `"`, CR or LF.
Anything else is refused: a non-string, an empty string, a longer one, and
those three, which RFC 4180 reserves for quoting and for ending a record, so
a delimiter equal to one of them leaves the record boundaries undefined."

§9.6 (`row-field-count`) refuses "a data row whose field count differs from
the header", and §13 reads record boundaries as RFC 4180's.

Split on `;`, the header is one field, `a,b`, and the row two, `1` and
`2,3`, so §9.6 refuses it. Split on a comma both are two fields: a reader
that ignores `delimiter` accepts this file.

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the field count is the only fault in the file and its sidecar,
so a reader that refuses it has refused for that reason or for one §13 does
not give. What the case does not pin is which reason the reader reports.
