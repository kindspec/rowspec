The sidecar declares `sku`, which is not a column. SPEC.md has no refusal
worded for an undeclared key column. Reading: the .mdtbl analogue for an
order column (§9.10, "not a stored column") is refused, and a key that
names nothing cannot be checked for refusal 5, so accepting it would
degrade a declared key into none (§4). `sku` is itself a valid `ident`, so
§9.16 does not apply.
