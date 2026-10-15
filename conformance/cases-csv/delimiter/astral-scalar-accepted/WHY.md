The sidecar's `delimiter` is U+1F600, written literally: four bytes in
UTF-8, and two code units in UTF-16. The CSV separates its fields with it.

§13: "**A fifth optional member, `delimiter`, names the field separator**: a
string of exactly one Unicode scalar value other than `"`, CR or LF.
Anything else is refused: a non-string, an empty string, a longer one, and
those three, which RFC 4180 reserves for quoting and for ending a record, so
a delimiter equal to one of them leaves the record boundaries undefined."

§9.6 (`row-field-count`) refuses "a data row whose field count differs from
the header", and §13 reads record boundaries as RFC 4180's.

It is one Unicode scalar value, so it is valid. A reader that measures the
string in UTF-16 code units, or in bytes, finds a longer string and refuses
this file.
