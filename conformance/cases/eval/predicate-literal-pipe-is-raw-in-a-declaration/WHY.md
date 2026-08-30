# Why this case exists

§4.1.3 scopes the escape precisely: "A reader splits **a table line** on
unescaped pipes and unescapes `\|` in each cell." A declaration line is not a
table line, so it is never split and never unescaped, and a literal in a
predicate is written raw.

The consequence is an asymmetry the spec does not spell out anywhere: the same
logical string is spelled `KS TV \| Action` in a data cell and
`"KS TV | Action"` in a declaration's predicate. Both spellings appear in this
one fixture, and they must match each other. Writing the predicate escaped
instead yields zero matches — silently, with no diagnostic. See
`design-findings/M0-adversarial-cases.md`.
