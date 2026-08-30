# Why this case exists

§4.2 rule 7's carve-out is the only path by which a decimal literal exists at
all: "a reader who munches `ident` maximally and only then classifies can never
produce the token `1.2` at all — `| gross = net * 1.2 |` fails to parse under
it. The carve-out above is what makes a decimal literal reachable."

The refusal cases beside this one (`ident-run-then-decimal-tail-refused`,
`second-decimal-point-in-an-operand-refused`) pin where the carve-out stops.
Without an acceptance pinned in the same family, an implementation that simply
refuses every `.` in a formula passes both of them — refusing the narrow
carve-out along with everything outside it. Here `1.5` must lex as one token,
classify as a literal in operand position, and multiply: `sum(scaled)` over
`4` and `2` is `9`, and no integer-only reading of the literal (`1`, or `15`)
produces it.
