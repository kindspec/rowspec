# Why this case exists

`signed = [ "-" *WSP ] literal` — the bracket is zero-or-one, exactly as
`factor`'s is, so a bound carries at most one minus.

§4.2 rule 7 already argues this for `factor` and the argument transfers without
change: "**A `factor` carries at most one unary minus.** ... Double negation has
an obvious arithmetic reading, which is exactly why it is worth refusing rather
than accepting silently: it is far more often a typo, a stray character from a
merge, or a `-` that lost its operand than it is an author asking for the
identity function."

A merge is the mechanism that matters here. `--` is what one side's `-` plus the
other side's `-` looks like after git resolves two edits to the same bound, and
a reader that folds it to `+` reports a plausible number for a line no author
wrote.
