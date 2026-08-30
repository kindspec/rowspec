# Why this case exists

§4.2 rule 10: "**Only the selected branch is evaluated.** **[CHOICE]**, and it
is the rule the feature exists for", followed by this exact table and the
sentence "Under eager evaluation of both branches every row with `qty` of `0` is
`#REF!(/0)`, and the guard the author wrote — the guard *every* spreadsheet
lineage would write — does nothing."

This is the canonical case, written as a single-cell assertion so the failure
names the cell rather than the total. `r_02` has `qty` of `0`: the selected
branch is the literal `0` and `total / qty` is never an operation the evaluator
performs. An implementation that evaluates both arms and then picks answers
`#REF!(/0)` here.

There is no other legitimate resolution. The spec's own words: "An
implementation that evaluates both branches is not merely slower; it computes a
different table."
