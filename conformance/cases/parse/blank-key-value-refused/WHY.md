# Why this case exists

The first row's key cell is blank. §4.1.9: "Column names, aggregate names,
the argument of `key` and `order`, and the values of the key column are
`ident`: one or more Unicode letters, marks or digits, or `_`." An empty
value is not one or more of anything, and §9.16 (`bad-identifier`) is the
entry for "a value of the key column" that is not an `ident`.

Only one key cell is blank, so §9.5 (`duplicate-row-id`) cannot apply, and
nothing else in §9 does. The same table with `r_1` in that cell is
`parse/key-in-bare-form-accepted`.
