# Why this case exists

`order := count(a where a = "1")`: an `order` declaration in aggregate form,
with a `where`.

The line matches the `declaration` production, because `rhs` does not tie the
function form to the left-hand name. It is still malformed. §4.1.11: "A
declaration is malformed (§9.12) if it contains `:=` and does not match
`declaration` — including a non-`key` name with no function, an unclosed
parenthesis, an unrecognised `order` construct such as `order := none()`, and
any `ident` violating rule 9." And: "§6 defines exactly two order states,
`order := by(c)` and the line omitted entirely; a third spelling is refused
rather than degraded into the second."

`count(...)` is not `by(c)`, so this is an unrecognised `order` construct, and
§9.12 (`malformed-declaration`) is the refusal. Reading the line as an
aggregate named `order` would degrade a failed recognition into a different
successful one, which §4 forbids: "A reader that cannot recognise a construct
MUST refuse it, and MUST NOT degrade a failed recognition into a different
successful one."

Nothing else in §9 applies. `key := id` names a stored column with distinct
`ident` values. §9.10 is about `order := by(c)`, and this is not that form.
`a` is a stored column, so the predicate names nothing missing, and `count`
is a known function, so §9.11 does not apply either.
