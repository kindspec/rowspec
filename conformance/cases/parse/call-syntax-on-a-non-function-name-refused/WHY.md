# Why this case exists

§4.2 rule 4: "a name before `(` that is in neither list is an unknown function
(§9.11), and a name not before `(` is a column reference, and no third case
exists."

`a` is a column, not one of the eight names of `rowrel-fn` and `agg-fn`, so
`a(b)` is an unknown function and the file is refused. Both implementations
refuse it; they disagree about which diagnostic, and §9 is explicit that "which
is reported is deliberately unspecified", so this case asserts only the refusal.
`rowspec_alt`'s "unknown aggregate function 'a'" is the one rule 4 describes.
