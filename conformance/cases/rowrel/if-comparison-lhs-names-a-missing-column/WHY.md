# Why this case exists

§8: "A reference to a name that does not exist evaluates to `#REF!(name)`", and
§4.2 rule 10: "an operand that is not a number — blank, text, or an error —
makes the whole `cond` that error".

An `ident` in a `comparison` is a reference like any other and gets no
dispensation for sitting in a position that "is not an expression and has no
value". The error carries `nope`, the originating name, not `x`.

The failure this catches is a comparison implemented as a predicate — a function
returning true or false — because a missing column then has to resolve to
*something* before the comparison can answer, and the available somethings are
`0` (§8: "A broken reference never evaluates to zero") and false (which selects
the else branch and returns a number). Both produce `0` for `s` in this file,
which is the value §1 calls plausible and §8 calls forbidden.

It is also the shape a typo takes. `if(qty > 0, …)` mistyped as `if(qtyy > 0, …)`
must not quietly become "always take the else branch".
