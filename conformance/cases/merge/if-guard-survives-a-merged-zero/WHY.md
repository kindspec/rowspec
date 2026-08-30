# Why this case exists

§14: "Merge cases assert on the **evaluated value** of the merged artifact, not
on git's exit code, because a clean merge with a wrong number is the failure
that matters."

Two authors edit two distant rows. Ours sets `r_0001`'s `qty` to `0`, which is
the guarded case §4.2 rule 10 exists for. Theirs changes `r_0004`'s `qty` from
`8` to `4`. Stock git merges both hunks cleanly, and the merged table must
evaluate to `0 + 5 + 5 + 4 = 14`.

The point is what an eager implementation reports: `#REF!(/0)`, arriving in a
file **neither author wrote**. Ours never saw `r_0004`'s new divisor and theirs
never saw the zero; each side's own file is fine under any implementation, and
the disagreement only exists after the merge. That is the shape §1 is about —
"a merge that is quietly wrong is worse than a merge that fails" — and it is why
laziness needs a merge case and not only an `eval` one.

The values are chosen so that no plausible wrong answer is `14`: eager
evaluation gives `#REF!(/0)`, the unmerged base is `17`, dropping theirs' edit
gives `12` and dropping ours' gives `19`. Treating the guard's `0` branch as a
blank that `sum` skips also gives `14` — but §8 forbids the skip, and
`eval/if-lazy-branch-does-not-poison-an-aggregate` asserts the `count` that
catches it.
