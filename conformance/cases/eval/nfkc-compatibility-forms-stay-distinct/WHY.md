# Why this case exists

The same §3 rule as `eval/nfkc-is-not-nfc-for-identifiers`, across the four
other compatibility classes a real corpus produces: a ligature (U+FB01 `ﬁ`
vs `fi`), a superscript digit (U+00B2 `²` vs `2`), a fullwidth letter
(U+FF21 `Ａ` vs `A`), and a Roman numeral (U+216B `Ⅻ` vs `XII`).

Each pair is NFC-distinct and NFKC-identical, so every one of them is a
duplicate column name (§9.2) under NFKC folding and two ordinary columns under
NFC. The expectations are powers of ten apart so that a fold in any single pair
is visible in exactly one aggregate.
