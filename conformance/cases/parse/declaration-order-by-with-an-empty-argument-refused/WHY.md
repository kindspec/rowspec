# Why this case exists

The declaration `order := by()` has an `order` argument that is not an `ident`:
it is empty.

§4.1's grammar for a declaration's right-hand side:

    rhs         = ident "(" *WSP arg *WSP ")" / ident
    arg         = ident [ 1*WSP "where" 1*WSP predicate ]
    ident       = 1*( LETTER / MARK / NUM / "_" )

§4.2: "a declaration's right-hand side matches `rhs` in its entirety or the
line is refused (§9.12). There is no partial parse and no fallback to text".

`ident` is `1*`, one or more characters, so an empty argument is not an `arg`.

Three of §9's entries apply, and the case names all three, since §9 says
"where several apply, the case names each of them, and reporting any one
passes":

- §9.12 `malformed-declaration`: "a line containing `:=` that does not match
  `declaration`".
- §9.16 `bad-identifier`: "an identifier — column name, aggregate name,
  `key`/`order` argument, or a value of the key column — that is empty, or
  that contains whitespace, a `Cf` format character, or any character outside
  `ident`". The `order` argument is named there explicitly.
- §9.10 `bad-order-column`: "`order := by(c)` where `c` is not a stored
  column". No stored column is named by an empty argument.

A key is declared, so §9.25 does not apply, and no formula uses a
row-relative operator, so §9.9 does not either.

§6 defines exactly two order states, `order := by(c)` and the line omitted,
and §4.1.11 says "a third spelling is refused rather than degraded into the
second". Reading this line as "no order" is that degradation.

The control is `parse/declaration-order-argument-that-is-an-ident-accepted`.
