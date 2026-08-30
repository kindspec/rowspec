# Why this case exists

§4.2: "**Tokenisation is maximal munch, and it happens BEFORE anything is
classified as a literal.** The two are not alternatives a tokeniser may try in
order: `1000_2999` is one token, never the literal `1000` followed by
`_2999`."

> This quoted the earlier wording, which added "`ident` is a strict *superset*
> of `literal`". §4.2 has since retracted that: `literal` admits `.` and
> §4.1.9 excludes it from `ident`, so the containment never held and an
> implementer following it could not tokenise `1.2`. Nothing about **this**
> case changes — the token here is all digits and underscores, where maximal
> munch is unaffected — and the case's expectation is untouched. Only the
> sentence it cites moved.

And the measurement the rule carries: "measured against 8,171 real spreadsheet
headers, 43 carry a name of this shape (`10_15` for a time of day, `1_0` for a
version, `31_03_2021` for a date, `1000_2999` for an amount band), and a host
language that reads `1000_2999` as a digit-separated number returned `10002999`
from a formula and the column's real total from `sum` — one file, one name, two
answers."

**Both assertions belong in one case.** `sum(<name>)` alone passes with the bug,
because a declaration's argument is a name position and never reached the
numeric path; the formula alone passes against a reader that mis-lexes both
consistently. The pair is what pins them to the same token.
