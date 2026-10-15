The sidecar's `delimiter` is a tab. The CSV is `a<TAB>b`, then `1,2<TAB>3`.

§13: "**A fifth optional member, `delimiter`, names the field separator**: a
string of exactly one Unicode scalar value other than `"`, CR or LF.
Anything else is refused: a non-string, an empty string, a longer one, and
those three, which RFC 4180 reserves for quoting and for ending a record, so
a delimiter equal to one of them leaves the record boundaries undefined."

§9.6 (`row-field-count`) refuses "a data row whose field count differs from
the header", and §13 reads record boundaries as RFC 4180's.

Split on tabs, both records are two fields; on a comma they are one and two.
The file is accepted.

Every fixture in this tree is named `input.csv`, so the default for a `.tsv`
or `.tab` name cannot be reached here; this case is about an explicit
`delimiter`.
