# Why this case exists — and it FAILS, on a defect it reproduced

§8: "A reference to a name that does not exist evaluates to `#REF!(name)`."
§4.2 rule 10, on the blank test: "it is the one place in the format where **a
blank cell** is data rather than an absence. **A blank cell's** text is the
empty string, so the equality is true." And, in the amended paragraph above it:
"**An error operand is an error under every operator, `=` and `<>` included.**
... It is *not* treated as blank."

`nope` is not a blank cell. It is not a cell at all, so its value is
`#REF!(nope)` by §8, and all three comparisons must carry that error.

**The reference implementation returns `1`, `0` and `0` instead** — measured, not
inferred:

    if(nope = "",  1, 0)  ->  1.0            (wanted #REF!(nope))
    if(nope <> "", 1, 0)  ->  0.0            (wanted #REF!(nope))
    if(nope = "x", 1, 0)  ->  0.0            (wanted #REF!(nope))

A missing column is given the empty string as its text, so it is
indistinguishable from a blank cell under **any** text comparison. Every other
path is correct in the same implementation, which is what makes this a defect
rather than a reading:

    if(nope = 0, 1, 0)    ->  #REF!(nope)    numeric RHS: correct
    if(nope > 0, 1, 0)    ->  #REF!(nope)    ordering:    correct
    | x = nope + 1 |      ->  #REF!(nope)    arithmetic:  correct

The same operand cannot be an error under `= 0` and blank under `= ""`. One of
the two is wrong and §8 says which.

**Why it matters more than a missing diagnostic.** The three spellings are the
three shapes a mistyped column name takes in real formulas, and each one
degrades to a plausible value rather than an error:

- `if(qtyy = "", 0, qty)` — the fallback fires in every row, and the author's
  "use this when that is missing" quietly becomes "always". §8: "A broken
  reference never evaluates to zero, empty, or a stale value."
- `if(regionn = "EU", 1, 0)` — a categorisation that matches nothing and totals
  `0`, which is §1's plausible number in every cell and an error in none.

The mechanism is worth naming because it is not a misreading of the spec, it is
a data-structure accident: a lookup that returns the same sentinel for "this
cell is empty" and "there is no such column" — which is what a dictionary
`.get()` returns in every host language — makes the two cases identical before
any rule gets to run.

`rowrel/if-blank-test-on-a-missing-column-is-still-an-error` is the single-cell
form of the first line, kept separately so the failure names the cell.
`rowrel/if-comparison-lhs-names-a-missing-column` is the ordering form, which
passes: `>` on a missing column is loud under every reading anyone would
implement, because there is nothing to compare. The `string` right-hand side is
the one operator that offers a wrong answer, and it offers three.
