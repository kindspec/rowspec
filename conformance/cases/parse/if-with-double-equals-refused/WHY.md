# Why this case exists

§4.2 rule 1: "`**`, `^`, `%`, `//`, `&`, `|`, `<<`, `>>`, `~`, `==`, `!=`, and
the words `or` and `not` are **refused** rather than given a meaning."

`eq-op = "<>" / "="`, and rule 10 adds nothing to that list. `==` is
equality in every host language an implementation is written in and in none of
the spreadsheet lineage this format comes from, so it is the spelling a user
types and a lenient parser accepts. Accepting it would give the format two
spellings of one operator, which §4.1.6 refuses on principle, and — worse — the
spelling rule of rule 10 hangs on reading the *right-hand side*, so a second
left-hand spelling buys nothing and costs a divergence.

Rule 1 is explicit that the list is not the rule: "**The rule is that `expr` is
exactly what the ABNF generates**, and an operator character appearing anywhere
else refuses the formula."
