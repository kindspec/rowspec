`columns` types `d` as `date`. Row `r1` holds the quoted field
`"2024-01-02<LF>"`, whose value is `2024-01-02` followed by a line
feed; row `r2` holds `2024-01-03`. No key is declared.

§13: "Each trimmed value of a named column is classified as an order
value is, and refused when its type is not the declared one: `text`
means a value matching neither `number` nor `date`, [...]"

An order value is classified by the sentence §13 gives for `order`: "Each
value of the column is trimmed of ASCII space and tab only (§4.1.4) [...]
A trimmed value is a `number` if it matches §4.1.6's `number`, a `date`
if it matches §4.1.7's `date`, and `text` otherwise".

§4.1: "ABNF, with `WSP = SP / HTAB` — ASCII space U+0020 and horizontal
tab U+0009, never the Unicode `White_Space` property — and `DIGIT =
%x30-39`, ASCII only." The productions are

    number      = [ "-" ] 1*DIGIT [ "." 1*DIGIT ]
    date        = 1*4DIGIT "-" 1*2DIGIT "-" 1*2DIGIT
                / 1*4DIGIT "/" 1*2DIGIT "/" 1*2DIGIT

Neither generates a trailing LF, and trimming removes only space and
tab, so a value ending in LF matches neither.

§13: "record boundaries are RFC 4180's. A quoted field runs to its
closing quote", so the LF inside the quotes is part of the value.

So `r1`'s value is text, not the declared `date`, and the file is
refused. A reader that matches `date` without anchoring the end of the
value accepts it.

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the type mismatch is the only fault in the file and its sidecar, so a
reader that refuses it has refused for that reason or for one §13 does not
give. What the case does not pin is which reason the reader reports.

## Identifier

This case asserts `refusal: "column-type-mismatch"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "a value of a column typed by `columns` that is not of that type, and an order column holding a value that is not of its `order_type`: §9.27 `column-type-mismatch`."

§9.27: "`column-type-mismatch`: a stored value whose type is not the type declared for its column — in §13's CSV profile, by the sidecar's `columns` or its `order_type` (§13)."

The earlier paragraph on `refusal_contains: ""` describes this case before §13 gave CSV-mode refusals identifiers; it now asserts `column-type-mismatch` instead.
