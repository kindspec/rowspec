# Why this case exists

The other row of the file asserted by
`rowrel/if-unselected-branch-dividing-by-zero-stays-per-row`, and the two are
written as separate cases because a `rowrel` case asserts one cell and
**per-row means two cells with different answers**.

`r_02` has `c` of `-5`, selects `a / z`, and `z` is `0`, so §4.2 rule 2 applies
in the ordinary way: "**Division by zero evaluates to `#REF!(/0)`**". One column,
one formula, one file: `10.0` in `r_01` and `#REF!(/0)` in `r_02`.

That is what "legitimately a per-row answer" means, and it is only visible in a
file where both answers occur. A case asserting either cell alone is satisfied
by an implementation that gives the whole column that one value — the number in
both rows if it never divides, the error in both if it always does — and each of
those is one of the two failures this pair exists to separate.

**This case is one half of a matched pair, and the pair is the test.** The two
files have the same shape — an `if` whose *unselected* branch is faulty, asserted
in the row that does not select it — and differ only in where the fault lives:

    | x = if(c > 0, c * 2, nope)  |   header fault  ->  #REF!(nope) in EVERY row
    | x = if(c > 0, c * 2, a / z) |   data fault    ->  10.0 in this row

`rowrel/if-unselected-branch-naming-a-missing-column-is-static` is the first.
`rowrel/if-unselected-branch-dividing-by-zero-stays-per-row` is the second, with
`rowrel/if-selected-branch-dividing-by-zero-is-an-error` asserting the other row
of that same file so the per-row-ness is visible rather than implied.

Neither half is safe alone. An implementation that resolves names lazily fails
the first and passes the second. An implementation that hoists *every* branch
fault to the whole column — the obvious over-correction once the first rule is
understood — passes the first and fails the second, and would turn the guard in
rule 10's own headline example into an error in every row. Only the line rule 10
draws passes both.

`rowrel/if-unselected-branch-may-overflow` is the third member of the family and
sits with the data half: whether `big * big` overflows depends on what is in the
`big` cell, so it is per-row too.
