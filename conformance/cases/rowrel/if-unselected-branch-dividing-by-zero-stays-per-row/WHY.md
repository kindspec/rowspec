# Why this case exists

§4.2 rule 10, in the [CHOICE] that made an unresolved name static: "Whether `b`
is zero in `if(c > 0, a / b, 0)` is a property of the **data**, so `#REF!(/0)`
is legitimately a per-row answer and **this rule does not touch it**."

`r_01` has `c` of `5`, so it selects `c * 2` and is `10`. Its own `z` is `0`, so
an implementation that evaluates both branches — or that has just been taught to
hoist a branch's fault to the whole column and applied it one construct too wide
— answers `#REF!(/0)` here.

**This is the case that stops the fix for the sibling from breaking the feature
rule 10 exists for.** The headline example in rule 10 is
`avg = if(qty > 0, total / qty, 0)`, whose entire purpose is that a zero divisor
in some rows does not poison the others. Make division by zero static and that
example is `#REF!(/0)` in every row, the guard does nothing, and rule 10's own
opening sentence — "An implementation that evaluates both branches is not merely
slower; it computes a different table" — is violated by the code written to obey
its later paragraph.

The difference is not which error it is. It is that `z` is a cell: an edit to
`r_01`'s `z` changes this answer, and no edit to any cell can change whether
`nope` resolves.

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
