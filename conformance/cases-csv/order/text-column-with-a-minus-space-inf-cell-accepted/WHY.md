The control for `order/text-column-with-one-*-cell-refused`. `o` holds
`apple`, `- inf` and `pear`. A key is declared.

`- inf` has a space between the sign and `inf`. Trimming removes `WSP` only
at the ends of a cell (§4.1.4), so the value is the four characters `- inf`,
which is not `inf` "after one leading `+` or `-`": the sign is followed by a
space, not by the spelling.

§9.10 lists "a non-finite spelling (`inf`, `nan`, `infinity`, any case, bare
or after one leading `+` or `-`)".

`- inf` is not one of those, bare or signed, and every value is text, so the
column has one type, no blank, and no listed spelling. The file is accepted.
