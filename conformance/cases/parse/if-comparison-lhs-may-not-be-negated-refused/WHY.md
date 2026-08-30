# Why this case exists

The same rule as `parse/if-comparison-lhs-must-be-an-ident-refused` with the
smallest possible violation: `comparison` begins with `ident`, and `-a` is a
`factor`, which `comparison` never reaches. §4.2 rule 7 confirms the side is a
name position — "the **left-hand `ident` of a `comparison`** (rule 10)" — and
that the asymmetry with the right-hand side "is deliberate".

It is worth a case of its own because the unary minus is the one piece of `expr`
that a comparison parser picks up by accident. A reader that calls its `factor`
routine for the left operand — a single line's difference from calling its
`ident` routine — accepts `-a > 0` and evaluates it correctly, so there is no
wrong number to find later. Only the refusal distinguishes the two grammars.

The hazard grew when `signed` was added. `signed = [ "-" *WSP ] literal` puts an
optional minus on the *right* of the operator, so an implementation now has a
real reason to have minus-handling code in its comparison parser, and reusing it
on the left is one line. `parse/if-comparison-rhs-negated-ident-refused` guards
the matching boundary on the other side.
