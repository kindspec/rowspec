# Why this case exists

`literal = 1*DIGIT [ "." 1*DIGIT ]` admits exactly one decimal point, and `.`
is not an operator in §4.2 rule 1's set, so `1.5.2` is neither one literal nor
two operands joined by anything. §9.20 refuses the header cell.

`5.` and `.5` fail the same way, and §4.1.6 already refuses both as cell values
— "a bare `.5` or `5.`" — so this pins that the expression language agrees with
the cell language about what a number looks like.
