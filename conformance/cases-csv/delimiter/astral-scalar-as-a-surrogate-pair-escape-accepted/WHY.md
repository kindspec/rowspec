The sidecar's `delimiter` is `"\ud83d\ude00"`: JSON's escape for U+1F600,
written as a UTF-16 surrogate pair (RFC 8259 §7). The CSV separates its
fields with U+1F600.

§13: "**A fifth optional member, `delimiter`, names the field separator**: a
string of exactly one Unicode scalar value other than `"`, CR or LF.
Anything else is refused: a non-string, an empty string, a longer one, and
those three, which RFC 4180 reserves for quoting and for ending a record, so
a delimiter equal to one of them leaves the record boundaries undefined."

§9.6 (`row-field-count`) refuses "a data row whose field count differs from
the header", and §13 reads record boundaries as RFC 4180's.

The string's value is the one scalar value U+1F600, so the delimiter is
valid, and both records split into two fields. A reader that counts the two
escapes as two characters refuses this file.
