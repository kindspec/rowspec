# Why this case exists

§4.1.9's `ident = 1*( LETTER / MARK / NUM / "_" )` admits `1e3` and `0x10`:
every character is a letter or a digit. §4.2's maximal-munch rule makes each one
a single `ident` token, and rule 7's operand-position tie-break applies only to
a token that is "*entirely* `1*DIGIT [ "." 1*DIGIT ]`", which neither is.

So each is an ordinary column name, and §4.1.6 has already refused both as
*number* spellings: "a leading `+`, exponent notation (`1e3`) ... a radix prefix
(`0x10`)".

**The answer is a loud `#REF!`, not a number and not a refusal.** This is the
over-correction guard: an implementation that refuses these formulas outright
would make a legal column name unusable, and one that reads them as numbers
returns 2000 for a formula whose author wrote a column reference. §8's ordinary
rule for an absent name gives the third answer, and it names the token the
author typed.
