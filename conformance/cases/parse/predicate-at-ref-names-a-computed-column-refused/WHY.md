# Why this case exists

§4.2 rule 5: "**Both `ident`s of an equality — the left-hand one and the one
after `@` — must name a stored column**, never a computed one. **[CHOICE]**
Comparison is on the cell's text (rule 6) and a computed column has no cell
text: §5 requires its data cells empty. The only available reading would compare
against the *rendered* form of a computed number, and §2 deliberately leaves
number formatting to the implementation — so one reader would write `20`,
another `20.00`, and the two would match different rows with no diagnostic on
either."

This was the open question from the previous pass, and refusal is the answer I
recommended: the competing answer is value-shaped, and a value that depends on
another implementation's number formatting is unstable across conforming
readers in a way a refusal is not. Before the fix the reference returned `0.0`
here — a predicate that matched nothing because a computed column has no cell
text to compare — which is the bill-of-materials failure mode exactly.

`rowspec_alt` returns `#REF!(g)`: loud, but still a value, and still one that
would become a number if the other reader rendered its computed cells.

This fixture puts the computed column on the `@` side; the previous one puts
it on the left. Rule 5 names both, so both need a case.
