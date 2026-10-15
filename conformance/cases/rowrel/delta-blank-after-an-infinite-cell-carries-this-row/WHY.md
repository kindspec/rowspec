# Why this case exists

Ordered by `n`, `a` is 9×10^313 (infinite as binary64) and then blank.
In the second row both operands of `a - prior(a)` give an error.

§7: "**`delta(c)` is read as `c - prior(c)`, so §8's leftmost rule decides
which error it carries: when this row's `c` and the preceding row's both give
an error, a blank included, `delta(c)` carries this row's.** A blank `c` here
beside a stored cell beyond binary64 in the row before is `#REF!(c)`, and the
same two rows the other way round are `#REF!(overflow)`."

This row's `a` is blank, so `d` is `#REF!(a)`.
`rowrel/delta-infinite-after-a-blank-carries-this-row` is the other order.
