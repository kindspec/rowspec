# Why this case exists

`order := by(a where a = "1")`: the `by` function with a `where`.

The `declaration` production generates the line, since `arg` admits
`ident [ 1*WSP "where" 1*WSP predicate ]` whatever the function. §6 does not
admit it: "§6 defines exactly two order states, `order := by(c)` and the line
omitted entirely; a third spelling is refused rather than degraded into the
second" (§4.1.11). `by(c)` takes a column and nothing else. A `where` filters
the rows an aggregate reads, and an order has no such filter.

Silently ordering by `a` and dropping the predicate, or ordering only the
rows where `a = "1"`, would each degrade a failed recognition into a
successful one, which §4 forbids.

Three of §9's entries apply, and the case names all three, since §9 says
"where several apply, the case names each of them, and reporting any one
passes". The reading is the one
`parse/declaration-order-argument-with-a-hyphen-refused` takes for
`order := by(id-x)`: §9.16's "`key`/`order` argument" and §9.10's `c` in
`order := by(c)` are the text between `by(` and `)`. Here that text is
`a where a = "1"`.

- §9.12 `malformed-declaration`. The line is not `by(c)`, so it is a third
  `order` spelling, and §4.1.11's list of malformed declarations includes
  "an unrecognised `order` construct such as `order := none()`". SPEC.md does
  not say which identifier refuses a third spelling that matches
  `declaration` (#225). `malformed-declaration` is the entry that sentence
  points to.
- §9.16 `bad-identifier`: "an identifier — column name, aggregate name,
  `key`/`order` argument, or a value of the key column — that is empty, or
  that contains whitespace, a `Cf` format character, or any character outside
  `ident`". §4.1.9 says "the argument of `key` and `order`" is an `ident`.
  `a where a = "1"` contains spaces, `=` and `"`.
- §9.10 `bad-order-column`: "`order := by(c)` where `c` is not a stored
  column". No stored column is named `a where a = "1"`.

Read the other way, with `a` as the argument and the `where` as something
separate, only §9.12 applies, because `a` is a stored `number` column with no
blank or non-finite cell, and it is a valid `ident`. Listing all three
identifiers passes an implementation under either reading. Naming only
`malformed-declaration` would fail an implementation that follows the
reading the suite already uses for `by(id-x)`.

`key := id` names a stored column with distinct values. `by` is the order
function, not an aggregate function, so §9.11 is not the refusal: the line is
not an aggregate declaration at all.
