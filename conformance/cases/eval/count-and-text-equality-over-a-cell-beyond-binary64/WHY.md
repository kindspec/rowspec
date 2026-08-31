# Why this case exists

§7: "a cell whose decimal spelling is finite but whose binary64 value is not
— four hundred digits, say — is `#REF!(overflow)` wherever it is used as an
**operand** (§8), and `count` never uses one as an operand. So `count` over
that cell is `1`."

The six aggregates are asserted TOGETHER because the contrast is the rule.
An implementation that converts the cell when it is *stored* rather than when
it is *used* makes the cell hold `#REF!(overflow)`, gets `s`/`mn`/`mx`/`av`
right for the wrong reason, and fails `n` (a `#REF!` actually present in the
column does poison `count`) and `t`. An implementation that never converts
gets `n` and `t` right and fails the other four. Only converting at use
passes all six.

`t` pins §7's companion sentence: `where big = "999…9"` matches, "because
rule 6 compares the cell's text and never consults its numeric value — so
nothing has used it as an operand."

The cell is the same four hundred nines as
`eval/stored-cell-beyond-binary64-is-overflow`, which pins the operand side;
this case pins the non-operand side that was settled later.
