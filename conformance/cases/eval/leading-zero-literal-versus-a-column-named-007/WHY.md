# Why this case exists

§4.2 rule 7: name positions "admit `ident` and have **no literal alternative**",
operand position "tries `literal` first, so a token matching `literal` is a
number."

`007` matches `literal` in its entirety, so in `out = 007 * 2` it is the number
7 and the answer is 14. In `sum(007)` it is the column, whose total is 50. One
token, two meanings, decided by position and by nothing else — and the column
named `007` is present, which is the only arrangement in which the rule differs
from "resolve to the column when one exists", the alternative §4.2 rejects
because it "makes the grammar a function of the table it is parsing".

It also pins that leading zeros do not disqualify a literal: `number` is
`[ "-" ] 1*DIGIT [ "." 1*DIGIT ]` with no leading-zero clause, and
`eval/number-leading-zeros-accepted` already fixes the cell-value side.
