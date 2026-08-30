# Why this case exists

§4.2 rule 7's carve-out extends a digit run across *one* `.` and the digit run
after it, and stops: "`1.2.3` is `1.2` followed by the same" — a character no
production admits — "so both are refused (§9.20) rather than being read as
something the author did not write."

`parse/malformed-numeric-literal-in-a-formula-refused` already refuses `1.5.2`
standing alone as a whole formula, where the literal grammar
(`1*DIGIT [ "." 1*DIGIT ]`) does the refusing by itself. Here the token sits in
operand position inside arithmetic, which is where a greedy float-scanning
lexer earns its keep: scan `1.2`, leave `.3` for later, or scan the host
language's idea of a number and swallow all of it. Either way the surviving
read is `a + 1.2` or a number the author did not write, and against this file
both accept and evaluate. The case demands a refusal.
