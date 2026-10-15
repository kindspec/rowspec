# Why this case exists

The control for `parse/key-names-a-missing-column-refused` and
`parse/key-names-a-computed-column-refused`: the same header, with
`key := id`. `id` is a stored column (§5: it has no formula), and its values
`r_1` and `r_2` are distinct `ident`s, so §4.1.11's rule that the key name a
stored column is met and nothing in §9 applies.

This pins that the check is about the named column, not about a computed
column merely being present in a table that declares a key.
