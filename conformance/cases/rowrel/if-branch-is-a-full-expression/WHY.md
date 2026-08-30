# Why this case exists

`cond = "if" "(" *WSP comparison *WSP "," *WSP expr *WSP "," *WSP expr
*WSP ")"` — each branch is a full `expr`, not a `primary` and not a literal.

`a + b * 2` with `a = 1, b = 3` is `7` and not `8`, so the case also pins that
§4.2 rule 1's precedence survives inside a branch: "Precedence, tightest first:
parentheses; unary `-`; `*` and `/`; `+` and `-`."

A parser that reads branches by scanning to the next comma at depth zero gets
this right; one that reads a branch as a single operand — the shortest thing
that works for `if(q > 0, 0, 1)`, which is the shape in every example — refuses
it or truncates at the `+`.
