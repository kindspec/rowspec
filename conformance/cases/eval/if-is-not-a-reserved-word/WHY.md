# Why this case exists

§4.2 rule 10: "`| x = if |` is a reference to a column named `if`", inheriting
rule 4: "**The function names are not reserved words.** ... recognised **only**
immediately before `(`".

Adding `if` to the language must not take the word away from tables that already
use it. Rule 4's [CHOICE] argues the general case — "reserving eight ordinary
nouns would refuse a table with a column named `count` or `min`, which is an
ordinary table" — and `if` is a worse offender than any of the eight, because a
column named `if` is a plausible header in a rules table and because `if` is a
keyword in every host language an implementation will be written in. A parser
that lexes identifiers through a keyword table gets this wrong for free.

`n := count(if)` puts the name in an aggregate argument as well as in an
operand, since §4.1's `arg` is a name position and a keyword-lexing reader
refuses it there too.
