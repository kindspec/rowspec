The sidecar's `delimiter` is U+212B ANGSTROM SIGN, whose NFC form is U+00C5
LATIN CAPITAL LETTER A WITH RING ABOVE. The CSV is `a<U+212B>b`, then
`1<U+212B>2<U+00C5>3`.

§13: "The delimiter is used as written, not NFC-normalised."

§9.6 (`row-field-count`) refuses "a data row whose field count differs from
the header", and §13 reads record boundaries as RFC 4180's.

Split on U+212B as written, the header is `a`, `b` and the row `1`,
`2<U+00C5>3`: two fields each, so the file is accepted. A reader that
normalises the delimiter to U+00C5 splits the header into one field and the
row into two; one that normalises the file as well splits the row into
three. Either refuses this file.
