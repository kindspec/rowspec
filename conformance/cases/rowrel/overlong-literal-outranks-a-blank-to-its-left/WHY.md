# Why this case exists

`1000…0` below is a literal of a `1` and 400 zeros, written out in the file;
its binary64 value is infinite. Row `r_1` has `k` = 1 and a blank `a`; row
`r_2` has `k` = 0 and `a` = 2. No `order` is declared, and file order and key
order agree. Several cases share these bytes.

§8: "**So is a numeric literal in a formula** whose binary64 value is
infinite: `| b = 1000…0 |`, with four hundred digits, is `#REF!(overflow)`.
The formula is not refused." and "**A formula holding such a literal is
`#REF!(overflow)` in every row, a row whose `if` takes the other branch
included, because whether a literal fits binary64 is a property of the header
alone".

§8: "**A header error outranks every other error, and the leftmost rule
chooses among header errors.** A header error is one whose cause is in the
header alone: a name that does not resolve (§4.2 rule 10) or a numeric literal
whose binary64 value is infinite (below)."

This case asserts `y = a + 1000…0` in `r_1`, where `a` is blank. The
literal is a header error and "outranks an error raised while evaluating a
row, a blank operand to its left included" (§8), so `y` is
`#REF!(overflow)`, not `#REF!(a)`.
