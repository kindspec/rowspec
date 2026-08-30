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

`0.1 + 0.2` is the canonical one: neither operand is representable in binary64,
and the sum lands one ulp above 0.3. A decimal implementation returns exactly
0.3, and the two readers disagree on a two-cell table.
