# Why this case exists

`cond = "if" "(" *WSP comparison *WSP "," *WSP expr *WSP "," *WSP expr
*WSP ")"`, and `comparison = ident *WSP ( order-op *WSP order-rhs / … )`.
Every one of those is `*WSP` — zero or more — so `if( c>0 , 1 , 0 )` and
`if(c > 0, 1, 0)` are one formula, and so is `if(c>0,1,0)`.

§4.2 rule 8: "`WSP` ... is permitted between any two tokens of an `expr` and is
never required there". The exceptions are enumerated and none of them is inside
`cond`: the only no-`WSP` rule rule 10 inherits is between `if` and its `(`,
which `parse/if-with-a-space-before-its-paren-refused` pins.

An implementation that lexes `>` only when it is surrounded by spaces, or that
requires `, ` with the space, refuses this file. That is a smaller language than
the format has, and §2's argument applies: two readers that disagree about which
files exist is the failure, whichever direction the disagreement runs.
