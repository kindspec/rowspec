# Why this case exists

§3: "Identifiers are compared after Unicode **NFC** normalisation". NFC, not
NFKC. `Nº` (U+00BA MASCULINE ORDINAL INDICATOR) and `No` are two distinct
identifiers under NFC and one identifier under NFKC, so a reader that folds
compatibility forms sees one column where the file declares two.

`Nº` is a real corpus header. With `ast.parse` doing the identifier work, the
formula `out = Nº` resolved to the `No` column and returned 22.0 while
`sum(Nº)` returned 11.0 — one file, one name, two readings, no diagnostic.

**Both assertions are load-bearing and must stay in one case.** `sum(Nº)` alone
passes with the bug present, because the aggregate path never went through
Python's identifier normalisation. `sum(out)` alone passes against a reader that
folds *everything* consistently. Only the pair pins that the formula and the
aggregate resolve the same name to the same column.
