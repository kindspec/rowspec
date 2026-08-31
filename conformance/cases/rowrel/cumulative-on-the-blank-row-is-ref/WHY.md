# Why this case exists

§7: on the blank row itself `cumulative(amt)` is already `#REF!(amt)` — the
running total needed a number this row does not have. An implementation that
treats a blank as contributing nothing (as `sum` legitimately does) answers
`5.0` here. The aggregate skip rule is §7's rule for `sum`/`min`/`max`/`avg`
over a column; it does not reach a row-relative step, which names this row's
cell and so asserts it is there.

See `rowrel/cumulative-after-a-blank-row-does-not-resume/WHY.md` for why the
family is six `rowrel` cases rather than one `eval` case.
