# Why this case exists

`order := by(a)`, a valid order declaration, followed by
`order := count(a where a = "1")`. Two refusals apply.

- §9.12 (`malformed-declaration`), for the second line. §4.1.11: "§6 defines
  exactly two order states, `order := by(c)` and the line omitted entirely;
  a third spelling is refused rather than degraded into the second", and a
  declaration is malformed when it is "an unrecognised `order` construct such
  as `order := none()`". `count(...)` is not `by(c)`.
- §9.4 (`duplicate-declaration`): "a duplicate `key` or `order`
  declaration". The file has two lines declaring `order`.

§9 leaves the choice to the implementation: "When one file violates several
refusals, *which* is reported is deliberately unspecified: the implementation
reports the identifier of any one that applies, and a case such as the
`parse/two-refusals-*` ones names every identifier that does." So `refusal`
lists both, and reporting either passes.

What fails is acceptance. A reader that takes the second line as an
aggregate named `order` sees one `order` declaration and one aggregate, and
accepts the file. `parse/order-in-count-form-with-where-refused` is the
second line on its own, and `parse/dup-order-decl` is two well-formed
`order` lines.

The first declaration is valid on its own: `a` is a stored `number` column
with no blank or non-finite cell, and `key := id` names a stored column with
distinct values.

§4.1.11 names `malformed-declaration` for a third `order` spelling that
matches `declaration` (#225): "`order := fn(arg)` is malformed (§9.12)
unless `fn` is `by` and `arg` is a bare `ident`", as
`parse/order-in-count-form-with-where-refused` sets out. §9.16
(`bad-identifier`) is not listed, for the reason given there: the suite
reads the text between `by(` and `)` as the `order` argument, and a line in
another function form has no such argument.
