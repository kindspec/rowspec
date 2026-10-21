# Why this case exists

`order := count(a where a = "1")`: an `order` declaration in aggregate form,
with a `where`.

The line matches the `declaration` production, because `rhs` does not tie the
function form to the left-hand name. It is still refused. §4.1.11: "§6
defines exactly two order states, `order := by(c)` and the line omitted
entirely; a third spelling is refused rather than degraded into the second."
`count(...)` is not `by(c)`, so this is a third spelling.

§4.1.11 names the identifier for a third spelling that matches `declaration`
(#225): "`order := fn(arg)` is malformed (§9.12) unless `fn` is `by` and
`arg` is a bare `ident`, whatever `fn` is", with
`order := count(a where a = "1")` among its examples, and §9.12's list
includes "an `order :=` in a function form other than `by(c)`". So the case
names §9.12 (`malformed-declaration`). Reading the
line as an aggregate named `order` would degrade a failed recognition into a
different successful one, which §4 forbids: "A reader that cannot recognise a
construct MUST refuse it, and MUST NOT degrade a failed recognition into a
different successful one."

Nothing else in §9 applies. `key := id` names a stored column with distinct
`ident` values. §9.10 is about `order := by(c)`, and this is not that form.
`a` is a stored column, so the predicate names nothing missing, and `count`
is a known function, so §9.11 does not apply either.

§9.16 (`bad-identifier`) is not listed. `parse/order-by-with-a-where-refused`
and `parse/declaration-order-argument-with-a-hyphen-refused` list it because
they read the text between `by(` and `)` as the `order` argument, which is
what `c` is in `order := by(c)`. A line in another function form has no such
`c`, and the suite does not read a function's text as the argument in that
case: `parse/key-in-aggregate-form-with-where-refused`
(`key := sum(id where a = "1")`) and `parse/key-in-by-form-refused`
(`key := by(id)`) name `malformed-declaration` alone, although neither
`sum(id where a = "1")` nor `by(id)` is an `ident`.
