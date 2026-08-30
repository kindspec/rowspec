# Why this case exists

`comparison = ident *WSP ( order-op *WSP order-rhs / eq-op *WSP eq-rhs )`. The
left-hand side is an `ident` and nothing else — not an `expr`, not a `primary`,
and so not a `cond`.

This is a place where rule 10 is *narrower* than it reads. "`if` is a `primary`,
and a comparison exists nowhere else" makes `if` compose everywhere an operand
goes; the left of a comparison is not one of those places, because `comparison`
does not descend through `primary`. A parser that implements `comparison` as
`expr order-op expr` — the obvious shape, and the one every host language uses —
accepts this file, and nothing downstream ever notices, because the construct
evaluates perfectly well. The divergence appears only when a stricter reader
refuses a file the lenient one wrote, which is §2's interoperability bug.

**This case was written when the asymmetry looked like it might be an
oversight.** It is not: §4.2 rule 7 now says so, in the course of settling a
different question. "The two sides of a comparison ... read a bare `3`
differently, which is the same asymmetry `equality` already has in a `where`
predicate — `ident` on the left, a value on the right — and **it is deliberate**:
the left of a comparison is the thing being tested and the right is what it is
tested against." Rule 7 also lists "the **left-hand `ident` of a `comparison`**"
among the name positions, which only makes sense if that side is an `ident` and
can be nothing else.

`parse/if-comparison-lhs-may-not-be-negated-refused` is the same rule with the
smallest possible violation.
