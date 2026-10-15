The control for `order/text-column-with-one-*-cell-refused`. `o` holds
`apple`, `--inf` and `pear`. A key is declared.

`--inf` carries two leading signs, and §6 admits "one leading `+` or `-`".

§9.10 lists "a non-finite spelling (`inf`, `nan`, `infinity`, any case, bare
or after one leading `+` or `-`)".

`--inf` is not one of those, bare or signed, and every value is text, so the
column has one type, no blank, and no listed spelling. The file is accepted.
