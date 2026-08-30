# Why this case exists

§4.2 rule 5: "The aggregated column itself carries no such restriction:
`sum(total where region = @region)` over a computed `total` is well-formed and
rule 9 gives it a value." An `if`-computed column is a computed column, so the
same sentence covers it.

The arithmetic is chosen so that every part has to be right. `big` is `200`,
`0`, `300`. `rt` is `200` for both EU rows and `300` for the US row, so
`s = 200 + 200 + 300 = 700`.

Three separate errors each produce a different plausible total, and none is an
error value: an implementation that reads `big` eagerly-but-wrongly and gives
`r_02` its `amt` of `50` reports `800`; one that mis-binds `@region` to the
candidate row — rule 5's "most dangerous thing in this section", which "turns
every group aggregate into a grand total" — reports `1500`; one that skips
computed columns in the aggregated position reports `0`.

Rule 5's binding rule is what makes `700` the answer: the `@` references are
"bound **once, to the row whose cell is being computed**, and held fixed while
the aggregated column is scanned over **every** row of the table."
