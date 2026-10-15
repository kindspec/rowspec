# Why this case exists

The header cell is `c = cumulative`, a space, then `(n)`, and the table
declares **no** `order`. A key is declared and `n` is a stored column.

§4.2 rule 4: the eight names of `rowrel-fn` and `agg-fn`, and `if`, "are
recognised **only** immediately before `(`, with no `WSP` between the two."
Rule 8 lists "**no** `WSP` between a function name and its `(`" among the
places where whitespace is not optional, and §4.1's `WSP` is "ASCII space
U+0020 and horizontal tab U+0009". Rule 4 again: "a name not before `(` is a
column reference ... A name before `(` that is a `rowrel-fn` with no
declared order is §9.9."

So `cumulative` here is not a function name: a space stands between it and
`(`, and it is read as a column reference followed by a parenthesised group.
`expr` does not generate an `ident` followed by `(`, and `rowrel-call =
rowrel-fn "(" ...` admits no whitespace before the parenthesis, so the
right-hand side is not a `formula`. §9.20 (`malformed-formula`) applies.

§9.9 (`rowrel-without-order`) refuses "a row-relative operator with no
declared order". There is none here: the only name a reader could take for
one is not immediately before `(`, so by rule 4 it is not a `rowrel-fn`
call, and rule 4's sentence about §9.9 names "a name before `(`", which this
is not. `refusal` is therefore `malformed-formula` alone.

The sibling `parse/cumulative-with-a-space-before-its-paren-refused` makes
the same point with an order declared, where §9.9 could not apply in any
reading. Here it could only apply by reading `cumulative (` as a call, which
is the reading rule 4 forbids, so a reader that reports §9.9 has recognised
a call the grammar does not generate.
