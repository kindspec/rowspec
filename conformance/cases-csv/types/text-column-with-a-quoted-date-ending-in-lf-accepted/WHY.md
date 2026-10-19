The control for `types/date-column-with-a-quoted-date-ending-in-lf-refused`.
`columns` types `d` as `text`. Row `r1` holds the quoted field
`"2024-01-02<LF>"`; row `r2` holds `later`. No key is declared.

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

Both values match neither `number` nor `date`, so both are `text`, the
declared type, and the file is accepted. A reader that matches `date`
without anchoring the end reads `r1` as a date in a `text` column and
refuses this file.
