# Why this case exists

The aggregate form of `rowrel/if-unselected-branch-naming-a-missing-column-is-static`,
on the same bytes.

§4.2 rule 10: "**A name that does not resolve is `#REF!(name)` in EVERY row,
even where the branch naming it is not selected.**" §8: "An aggregate over any
column containing a `#REF!` is itself `#REF!` — **it must not sum the values it
can read**."

Under the reading rule 10 rejected, `r_01` is `10` and `r_02` is `#REF!(nope)`,
so `s` is `#REF!(nope)` either way and the total alone cannot tell the readings
apart — which is exactly why the single-cell case exists and is asserted on
`r_01`. What this case adds is the two aggregates over a column where **no row
is clean**: `s` may not be `10`, and `n` may not be `1` or `2`.

`n` is the sharper of the two. §7 carves `count` out of coercion — it "counts
rows and never coerces" — but not out of poisoning: it is poisoned by "a `#REF!`
actually present in the column", and under this rule one is present in every
row. An implementation that resolves names lazily and then counts the rows it
managed to compute reports `1`, a number smaller than the table, which is §1's
plausible smaller total.

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
