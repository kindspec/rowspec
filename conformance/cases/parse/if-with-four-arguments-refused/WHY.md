# Why this case exists

The over-supplied counterpart of `parse/if-with-two-arguments-refused`. `cond`
takes three parts; a fourth is not generated.

It catches a different bug from the two-argument case: a parser that splits the
argument list on commas and then reads the first three entries accepts this file
and silently discards `3`. §4.2's whole-cell recognition rule forbids that
directly — "A header cell's right-hand side matches one alternative of `formula`
**in its entirety** or the cell is refused (§9.20). There is no partial parse".
