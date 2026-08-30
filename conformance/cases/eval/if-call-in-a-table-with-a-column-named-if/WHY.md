# Why this case exists

The two readings of `if` in one header cell: the first `if` is immediately
before `(` and is the function, the second is not and is the column holding `7`.

§4.2 rule 4: "a name before `(` that is in neither list is an unknown function
(§9.11), and a name not before `(` is a column reference, and **no third case
exists**." Rule 10 puts `if` under that rule "unchanged".

This is the case that separates a correct implementation from one that merely
avoids a keyword table. A reader that special-cases the *string* `if` anywhere
it appears cannot evaluate this cell at all; a reader that resolves `if` to the
column everywhere cannot parse the call; only the position rule gives `7` for
`r_01` and `0` for `r_02`.

`eval/if-is-not-a-reserved-word` covers the name with no call in the file, which
a reader can pass by never having heard of `if`. This one cannot be passed that
way.
