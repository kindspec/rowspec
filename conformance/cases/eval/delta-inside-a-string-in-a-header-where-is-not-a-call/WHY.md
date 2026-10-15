# Why this case exists

No `order` is declared. The only mention of `delta(` in the file is inside a
string literal in a header cell's `where`:

    | t = sum(amt where note = "delta(amt)") |

§4.2's grammar:

    rowrel-call = rowrel-fn "(" *WSP ident *WSP ")"
    string      = DQUOTE *( char - DQUOTE ) DQUOTE

A `string` is any run of characters other than `"`, so `"delta(amt)"` is a
string and nothing inside it is a call. §9.9 (`rowrel-without-order`) refuses
"a row-relative operator with no declared order", and there is no
row-relative operator here: the formula is a `group-call`, `sum(amt where note = "delta(amt)")`. The file is accepted.

The data cells holding `delta(amt)` are data, and the predicate compares text
(§4.2 rule 6: "Equality compares text, never numbers"). Rows `r_01` and `r_03` hold `delta(amt)` and row `r_02` holds `x`, so `t` is 5 + 11 = `16` in every row and `max(t)` and `min(t)` are both `16`.

A reader that looks for `delta(` in the header text, rather than for a
`rowrel-call` in the parsed formula, refuses a valid file. The control, a
real `prior` call with no order, is
`parse/prior-call-beside-a-string-mention-without-order-refused`.
