# Why this case exists

The formula is `delta`, a tab, then `(a)`, in a table with a declared
order.

§4.2 rule 4: the eight names of `rowrel-fn` and `agg-fn`, and `if`, "are
recognised **only** immediately before `(`, with no `WSP` between the
two." Rule 8 lists "**no** `WSP` between a function name and its `(`"
among the places where whitespace is not optional, and §4.1's `WSP`
is "ASCII space U+0020 and horizontal tab U+0009".

Rule 4: "a name not before `(` is a column reference". So `delta` here is a
column reference followed by a parenthesised group, which `expr` does not
generate, and `rowrel-call = rowrel-fn "(" …` does not admit the
whitespace. §9.20 (`malformed-formula`) applies. The order is declared and
`delta` is not read as a call, so §9.9 does not.
