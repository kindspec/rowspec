`o` is the order column and `id` the key. Row `r1` holds the quoted
field `"2024-01-02<LF>"`, whose value is `2024-01-02` followed by a
line feed; row `r2` holds `2024-01-03`.

§13: "`order` names the column that orders the rows, and §6's order
rules apply to it. `key` is then required (§9.25). Each value of the
column is trimmed of ASCII space and tab only (§4.1.4), so a leading or
trailing non-ASCII space is part of it. A trimmed value is a `number` if
it matches §4.1.6's `number`, a `date` if it matches §4.1.7's `date`, and
`text` otherwise; no value matches both."

§13: "The column is refused (§6, §9.10) when it mixes types, [...]"

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

So `r1`'s value is text and `r2`'s is a date: the column mixes types
and is refused. A reader that matches `date` without anchoring the end
of the value, as Python's `re.match` with `$` does (`$` also matches
before a final newline), reads both as dates and accepts the file.

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the mixed types is the only fault in the file and its sidecar, so a
reader that refuses it has refused for that reason or for one §13 does not
give. What the case does not pin is which reason the reader reports.

## Identifier

This case asserts `refusal: "bad-order-column"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "an `order` naming no column of the file, and an order column that mixes types, is blank in any row, or holds a non-finite value: §9.10 `bad-order-column`, whose "`c` is not a stored column" is the first."

§9.10: "`bad-order-column`: `order := by(c)` where `c` is not a stored column, is computed, mixes types, is blank in any row, or holds a non-finite spelling (`inf`, `nan`, `infinity`, any case, bare or after one leading `+` or `-`) in any row (§6)."

The column mixes types, and no `order_type` or `columns` is declared, so §9.27 cannot apply.

The earlier paragraph on `refusal_contains: ""` describes this case before §13 gave CSV-mode refusals identifiers; it now asserts `bad-order-column` instead.
