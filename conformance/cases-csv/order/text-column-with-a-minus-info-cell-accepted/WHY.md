The control for `order/text-column-with-one-*-cell-refused`. `o` holds
`apple`, `-info` and `pear`. A key is declared.

`-info` is a sign before `info`, which is none of `inf`, `nan` or
`infinity`.

§9.10 lists "a non-finite spelling (`inf`, `nan`, `infinity`, any case, bare
or after one leading `+` or `-`)".

`-info` is not one of those, bare or signed, and every value is text, so the
column has one type, no blank, and no listed spelling. The file is accepted.
