# Why this case exists

§4.2 rule 2: "**Arithmetic is IEEE 754 binary64.** Every operand is converted to
a binary64 double and every operator is the corresponding IEEE 754 operation
under round-to-nearest-even."

The rule exists because it was once left open: "measured against a corpus of
cached spreadsheet results, 501 cells were ones a 40-digit decimal
implementation reproduced exactly and binary64 did not — so a decimal reader and
a binary64 reader were both conformant and disagreed in the last digit."

These are the two shapes of that disagreement, chosen so a decimal reader fails
them and no rounding mode saves it. Note what the case is *not*: §4.2 says
"Matching any particular spreadsheet's last digit is explicitly **not** a goal
(§1); agreement between conforming implementations is." These expectations are
binary64's answers, not Excel's.

2^53 + 1 is the smallest integer binary64 cannot represent. Round-to-nearest-even
returns 2^53 unchanged, so adding one to this cell changes nothing. A decimal
implementation returns 9007199254740993, and an implementation that carried
integers exactly while calling itself binary64 would too.

Both operands are written as plain digits, so nothing here depends on how a
reader spells large numbers — only on the arithmetic.
