# Why this case exists

The file has a lone `CR` between two data rows of the table.

## Re-derived at `52be434`

SPEC.md #264 changed §9.15: a lone `CR` in a `.mdtbl` file is decided before any line is classified, and the line holding it is classified as though the `CR` were not there. Under the earlier text this case listed `lone-cr`, `malformed-table-line` and `unclassified-line`, with no `WHY.md`; it now asserts `lone-cr` and `row-field-count`.

§9.15: "`lone-cr`: a lone `CR` (§3). Like §9.14 it is a property of the bytes, decided before any line is classified, so in a `.mdtbl` file a lone `CR` is never also a character of the line holding it: that line is classified as though the `CR` were not there. Without this, every lone `CR` in a `.mdtbl` file would also be §9.12, §9.18 or §9.19, because `char` excludes `CR` and the line holding one matches no alternative of `line`."

§3: "A lone `CR` is refused: it makes two rows share one git line, which breaks the format's founding rule that one line is one row."

§4.1: "eol = LF / CRLF ; a lone CR is refused (§3)"

§4.1: "table-line = *WSP "|" 1*( cell "|" ) *WSP eol"

§4.1: "cell = *( escaped / ( char - "|" ) )"

§4.1.3: "A reader splits a table line on unescaped pipes and unescapes `\|` in each cell"

§9.6: "`row-field-count`: a data row whose field count differs from the header"

§9: "A conformance case that names one identifier is therefore a case in which exactly one refusal applies; where several apply, the case names each of them, and reporting any one passes."

The `CR` ends no line: lines end at `LF` or `CRLF` only. So rows `r_0002` and `r_0003` are one line, and set aside the `CR` reads it as

    | r_0002 | gadget | 20 | 6.00 |  || r_0003 | sprocket | 8 | 15.00 |  |

That is a well-formed `table-line`: both outer pipes are present, and `||` is an empty cell, which `cell` generates. It lies inside the table's contiguous run, so §9.18 (`malformed-table-line`) and §9.19 (`unclassified-line`), listed before, no longer apply. Split on its unescaped pipes it has 11 fields against the header's 5, so it is a data row whose field count differs from the header: §9.6 (`row-field-count`). Row `r_0003` is not a row of its own, so no key is repeated. The `total` field of that row is blank, and no other cell of a computed column holds a value. Both §9.15 and §9.6 apply.

Re-derived from SPEC.md at rowspec `52be434` alone, by an author who saw no
implementation. SPEC.md sha256
`7e9fb663c7391f4c393c9d9eb8b5c673f4fb22f221c4b29b3119aaf3a36d3884`.
