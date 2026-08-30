# Why this case exists

`primary = literal / ident / "(" *WSP expr *WSP ")"` is recursive, so
parentheses nest to any depth and a parenthesised sub-expression is an operand
like any other. §4.2 rule 1 puts parentheses at the tightest precedence.
