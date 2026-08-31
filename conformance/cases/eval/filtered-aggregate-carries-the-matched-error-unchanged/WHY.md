# Why this case exists

§8: "**An aggregate poisoned by a `#REF!` among its operands carries THAT
error, unchanged.** `sum(v where g = "A")` over a matched `#REF!(/0)` is
`#REF!(/0)`, not a relabelled `#REF!(v)`."

The perturbation that matters is not error-versus-number but which error:
`#REF!(v)` names a well-formed computed column and sends the reader to
inspect its formula, when the thing to fix is the `d` of `0` in row `r_01`.
An implementation that reports aggregate poisoning generically — "column `v`
is bad" — passes every case where the poison originated as a broken name in
`v`'s own formula (there the two spellings coincide) and fails only where the
poison is per-row data, which is what `/0` is.

`eval/where-excluded-row-ref-does-not-poison` brushes this value in passing;
this case exists so the relabelling rule is pinned by a case that says so,
and survives if that one is ever reorganised around its own point (exclusion).
