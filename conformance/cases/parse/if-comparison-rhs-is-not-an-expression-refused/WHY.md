# Why this case exists

`order-rhs = literal / ident`. Not an `expr`, not a `term`, not a `factor` — one
token.

`a > b + 1` is the shape a user writes and a general-purpose expression parser
generates for free, since `comparison` is almost always written as
`expr op expr`. It evaluates to something perfectly sensible, so an
implementation that accepts it produces no wrong answer in this file and no
diagnostic in any other — it simply speaks a larger language than the format
has, and the divergence appears only when a stricter reader refuses a file the
lenient one wrote.

That is the interoperability failure §2 names: "An undocumented degree of
freedom becomes an interoperability bug the moment two implementations meet in
one repository." §4 states the discipline: a reader that cannot recognise a
construct MUST refuse it.
