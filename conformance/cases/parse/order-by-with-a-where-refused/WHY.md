# Why this case exists

`order := by(a where a = "1")`: the `by` function with a `where`.

The `declaration` production generates the line, since `arg` admits
`ident [ 1*WSP "where" 1*WSP predicate ]` whatever the function. §6 does not
admit it: "§6 defines exactly two order states, `order := by(c)` and the line
omitted entirely; a third spelling is refused rather than degraded into the
second" (§4.1.11). `by(c)` takes a column and nothing else. A `where` filters
the rows an aggregate reads, and an order has no such filter, so this is not
`by(c)`. It is an unrecognised `order` construct, which §4.1.11 lists among
malformed declarations: "an unrecognised `order` construct such as
`order := none()`". §9.12 (`malformed-declaration`) is the refusal.

Silently ordering by `a` and dropping the predicate, or ordering only the
rows where `a = "1"`, would each degrade a failed recognition into a
successful one, which §4 forbids.

The case names one identifier. The column the `where` is attached to, `a`, is
a stored column of one type (`number`) with no blank or non-finite cell, so
§9.10 (`bad-order-column`) does not apply to it, and it is a valid `ident`,
so §9.16 does not either. `key := id` names a stored column with distinct
values. `by` is the order function, not an aggregate function, so §9.11 is
not the refusal: the line is not an aggregate declaration at all.
