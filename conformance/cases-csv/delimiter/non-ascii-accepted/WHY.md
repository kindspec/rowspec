The sidecar's `delimiter` is `¦` (U+00A6 BROKEN BAR), two bytes in UTF-8.
The CSV separates its fields with it, and the row's first field holds a
comma.

§13: "**A fifth optional member, `delimiter`, names the field separator**: a
string of exactly one Unicode scalar value other than `"`, CR or LF.
Anything else is refused: a non-string, an empty string, a longer one, and
those three, which RFC 4180 reserves for quoting and for ending a record, so
a delimiter equal to one of them leaves the record boundaries undefined."

§9.6 (`row-field-count`) refuses "a data row whose field count differs from
the header", and §13 reads record boundaries as RFC 4180's.

U+00A6 is one Unicode scalar value, so the delimiter is valid. Split on it,
both records are two fields, so the file is accepted. A reader that requires
a one-byte or ASCII delimiter refuses it.
