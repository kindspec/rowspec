# Why this case exists

§4.2 rule 10: "**`signed` admits whitespace after its `-`; a cell's `number`
does not.** `if(a > - 1, …)` is well-formed while a cell spelled `- 1` is not
a number and is `#REF!` under §8."

The two halves are asserted in one table because the asymmetry is the rule:
one grammar (`signed`, in an expression, where rule 8 makes `WSP` free
between tokens) and one value syntax (§4.1.6's `number`, one spelling per
value) read the same three characters differently, and neither bends for the
other. `sx` fails an implementation that refuses the spaced bound;
`sy`/`sb` fail one that reuses its lenient bound parser on cell values and
reads `- 1` as minus one — `sy` would then be `-2.0` and `sb` `-1.0`, both
plausible numbers.
