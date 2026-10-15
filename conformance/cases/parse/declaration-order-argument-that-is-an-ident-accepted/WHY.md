# Why this case exists

The control for `parse/declaration-order-argument-with-a-hyphen-refused` and
`parse/declaration-order-by-with-an-empty-argument-refused`.
`order := by(id_x)` names a stored column `id_x`, whose name is an `ident`
(§4.1.9 admits `_`), holding the numbers `1` and `2`. A key is declared.

None of §9.10's conditions holds: `id_x` is stored, not computed, of one type,
never blank, and holds no non-finite spelling. The line matches `declaration`,
so §9.12 does not apply, and §9.16 does not either. The file is accepted.
