# Why this case exists

SPEC.md §9.18: "a table line that does not match `table-line`, in particular one
lacking its closing `|` (§4.1.3)". The grammar is
`table-line = *WSP "|" 1*( cell "|" ) *WSP eol` -- the closing `|` is not
optional.

§4.1.3 gives the reason, and it is the strongest argument in the section:
"[CHOICE] The closing `|` is required rather than optional as in GFM: it is the
only thing that distinguishes a row truncated inside its final cell from a
shorter one, and the field-count refusal (§9.6) cannot see that truncation
because the field count does not change."

**Both implementations accept this file.** Neither is enforcing §9.18. A row cut
off mid-cell by a bad merge, a truncated write, or an editor that strips
trailing whitespace is read as a complete row with a shorter last value, and
every total computed from it is plausible and wrong.
