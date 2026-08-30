# Why this case exists

Three rules meeting on one cell.

§7: `cumulative(c)` is a running total "evaluated over the derived order and
never over file position". §6: "A row's position in the file is never an input
to any computation." The file lists `2024-01-02` first, so the derived order
reverses it: `r_02` is index 0 and `r_01` is index 1.

§4.2 rule 9: the argument of `cumulative` may be a computed column — "A formula
may name any column, stored or computed" — and rule 5's stored-only restriction
is scoped to `where` predicates, not to a `rowrel-call`'s argument.

So `flag` is `0` for `r_02` (its `a` is negative, the else branch) and `5` for
`r_01`, and the running total at index 1 is `0 + 5 = 5`.

Two wrong answers are both plausible numbers: `2` if the running total is taken
in file order (`5` then `5 + (-3)`, which additionally requires the `if` to be
wrong), and `-3` or `5` if `cumulative` reads `a` rather than `flag`. Neither is
an error value, and §4.1.7 records what this class of bug costs — "an overdraft
check reads a running balance of `55.0` where the truth is `5.0`".
