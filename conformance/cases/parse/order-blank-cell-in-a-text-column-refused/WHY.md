# Why this case exists

§9.10 refuses `order := by(c)` where `c` "**is blank in any row**", and the
entry says why the words are there: "Blank is listed explicitly because it is
not one of the three types §6 admits, so 'mixes types' reaches it only
through an argument rather than through the words."

This case is the input that makes the blank rule LOAD-BEARING. In
`parse/order-blank-cell-refused` the order column is otherwise numeric, so an
implementation that drops the blank rule and types the blank by inference —
not a `number`, not a `date`, therefore text — still refuses that file for
*mixing* number with text, and the case cannot tell the two readings apart.
Here every non-blank cell is text, so blank-as-text leaves the column
uniformly typed and the mixed-types check is satisfied: only §9.10's blank
rule stands between this file and an acceptance that sorts the blank wherever
the implementation's comparator happens to put it — handing a running
total's meaning "to whichever reader guessed", which is §6's own [CHOICE]
rationale for refusing.

A blank among dates does not need a sibling case: a blank is not a `date`
either, so that column is mixed and refused incidentally, exactly as the
numeric one is. Text is the one shape that separates the readings.

`refusal_contains` is `""` because §9.10 mandates the refusal without
mandating a message.
