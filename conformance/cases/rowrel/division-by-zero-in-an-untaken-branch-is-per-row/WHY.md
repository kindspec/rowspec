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

This case asserts `g = if(k > 0, 1, 1 / 0)` in `r_1`, where `k > 0`
selects `1`. §8: "Only the literal itself is a header error: an operation
on literals, such as `1 / 0`, is evaluated per row like any other." §4.2
rule 10: "**Only the selected branch is evaluated.**" So `g` is `1`.
`rowrel/division-by-zero-in-a-taken-branch-is-div-zero` is the other row.
