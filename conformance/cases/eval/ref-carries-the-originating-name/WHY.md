# Why this case exists

§8: "`#REF!(name)` carries the *originating* name — the column that could not be
resolved or whose value would not coerce, **not the column the error surfaces
in**."

The originating column is `a`: its cell holds `1,000`, which §4.1.6 refuses as a
number. `b` and `c` merely propagate. So both aggregates are `#REF!(a)`, at
every distance from the origin.

**The reference relabels at the second hop**: `sum(b)` is `#REF!(a)` and
`sum(c)` is `#REF!(b)` — the column the error surfaces in, which §8 names
explicitly as the wrong answer. `rowspec_alt` returns `#REF!(a)` for both.

One hop was already covered (`eval/ref-poisons-cumulative`,
`eval/thousands-separator-refused`), which is why this survived: the relabelling
is invisible until a third column is added. The diagnostic value is the whole
point of the rule — a reader who sees `#REF!(b)` goes and inspects `b`, which is
fine, and never reaches the cell that is actually wrong.
