# Why this case exists, and what it used to assert

§4.2 rule 10: "**A name that does not resolve is `#REF!(name)` in EVERY row,
even where the branch naming it is not selected.** `if(c > 0, c * 2, nope)` with
no column `nope` is `#REF!(nope)` throughout, not `c * 2` in the rows where `c`
is positive."

`r_01` has `c` of `5` and selects the first branch. It is still `#REF!(nope)`.

**This case was written asserting `10.0`, and the flip is the point of it.**
When it was written rule 10 said only that "Only the selected branch is
evaluated", and §8 framed an unresolved name as an *evaluation* result — "A
reference to a name that does not exist evaluates to `#REF!(name)`", a sentence
in a section about propagation. Under that text `nope` was never evaluated here
and `x` was `10`. The competing reading came from the static-analysis paragraph
below, which sweeps "the whole formula, both branches included" but says
"dependency and cycle analysis", and a missing name is neither a cycle nor
something a dependency graph can be built from. The document decided neither, so
two implementers would differ, and both readings produce values with nothing to
notice.

Rule 10 now decides it, and the reason it gives is a line neither reading had
drawn — **between the header and the data**:

> Whether `nope` resolves is a property of the header alone: it is knowable
> before a single row is read, it is the same for every row, and no edit to any
> cell can change it. Whether `b` is zero in `if(c > 0, a / b, 0)` is a property
> of the data, so `#REF!(/0)` is legitimately a per-row answer and this rule does
> not touch it. Errors that come and go with the data are ordinary; an error that
> comes and goes with the data while its *cause* sits unchanged in the header is
> not.

That distinction is what makes the old reading indefensible rather than merely
unfashionable. Under it a column is well-formed until a merge adds the first row
that takes the other branch, and then that column and every aggregate over it are
poisoned by a commit touching no formula and no header — §1's failure with a new
trigger. It also delays the diagnostic: a mistyped column name surfaces when a
row happens to select that branch, not when it is written.

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
