# Why this case exists

§4.2 rule 10: "`<`, `<=`, `>`, `>=` are **numeric, always**. Both operands are
converted as §4.2 rule 2 converts them, and an operand that is not a number —
blank, text, or an error — makes the whole `cond` that error".

A date cell is not a number. §4.1.6 defines `number` and `2024-01-02` does not
match it; §4.1.7 gives dates their own production and their own comparison rule,
"**Dates compare as the integer tuple `(y, m, d)`, never as strings**" — but
that rule is scoped to §6's order column, which is where the format sorts dates.

`>` in a `cond` is not that. An implementation that reuses its §6 comparison
machinery inside `if` — an attractive move, since it already exists and already
handles dates correctly for `order := by(c)` — gets a *true* here where the
format gets an error. Which way it goes depends on today's date arithmetic, so
the same file changes answer depending on the constant it is compared against,
and there is no error anywhere to notice.

If date-aware ordering inside `if` is wanted, it is a proposal with its own
evidence — rule 1's standard for `**` applies: "Adding it is a proposal, not a
clarification." Rule 10 as written has one ordering rule and it is numeric.
