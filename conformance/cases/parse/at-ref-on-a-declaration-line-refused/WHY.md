# Why this case exists

§4.2 rule 5: "**`@` is legal in exactly one place: the right-hand side of an
equality inside a `where` predicate in a header cell.** Not in arithmetic, **not
on a declaration line**, and not in the left-hand side of an equality."

And the spec's own verbatim example of the refusal:
"`g := sum(amt where r = @s)` is a malformed declaration (§9.12)."

The reason is stated with it: "a table-level aggregate has no current row for
`@` to refer to. Any reading an implementation invents — **and the reference
implementation invents one, comparing each candidate row against itself** —
makes the predicate a filter the author did not write."

The reference still accepts this file and returns `5.0`, which is that invented
reading: it matched only the row where `r` and `s` happen to be equal. There is
no row the author meant, so there is no number to report.
