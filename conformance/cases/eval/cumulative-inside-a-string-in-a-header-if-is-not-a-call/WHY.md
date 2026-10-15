# Why this case exists

No `order` is declared. The only mention of `cumulative(` in the file is inside a
string literal in a header cell's `if`:

    | x = if(note = "cumulative(amt)", amt, 0) |

§4.2's grammar:

    rowrel-call = rowrel-fn "(" *WSP ident *WSP ")"
    string      = DQUOTE *( char - DQUOTE ) DQUOTE

A `string` is any run of characters other than `"`, so `"cumulative(amt)"` is a
string and nothing inside it is a call. §9.9 (`rowrel-without-order`) refuses
"a row-relative operator with no declared order", and there is no
row-relative operator here: the formula is an `expr` whose `primary` is a `cond`, whose `comparison` has a `string` right-hand side. The file is accepted.

The data cells holding `cumulative(amt)` are data, and the predicate compares text
(§4.2 rule 6: "Equality compares text, never numbers"). Rows `r_01` and `r_03` hold `cumulative(amt)` and take the first branch, `amt`; row `r_02` holds `y` and takes `0`. So `x` is `5`, `0` and `11`, `sum(x)` is `16` and `max(x)` is `11`.

A reader that looks for `cumulative(` in the header text, rather than for a
`rowrel-call` in the parsed formula, refuses a valid file. The control, a
real `prior` call with no order, is
`parse/prior-call-beside-a-string-mention-without-order-refused`.
