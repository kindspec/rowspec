# Why this case exists

§7: "An aggregate's value is defined on the multiset of its operands, never on
an accumulation order. `sum(c)` is the correctly-rounded binary64 value of the
exact mathematical sum." And §6: "a row's position in the file is never an
input to any computation."

The same four cells as `eval/sum-huge-cancellation-signs-interleaved` —
exact sum `0` — but with the two positives first. A left-to-right binary64
accumulator reaches `2e308` after two rows, which is an infinity, and reports
`#REF!(overflow)`; the interleaved sibling reports `0`. Two answers for one
multiset is the divergence §7's rule exists to close, and a merge is how the
reordering happens in practice (`merge/reordering-merge-keeps-the-sum`).

This case also pins §7's first named consequence directly: "a sequence whose
partial sums leave binary64 range but whose exact sum does not is a number,
not an overflow." `#REF!(overflow)` is the *wrong* answer here twice over — a
naive accumulator gives it, and so does an exact-summation routine that flags
*intermediate* overflow (a host `fsum` raising on these bytes is the shape
already recorded in `eval/aggregate-overflow-from-finite-cells/WHY.md`). The
value exists; the answer is `0`.
