# Why this case exists

SPEC.md §4.1.6: "A cell is read as a number only if it matches `number`.
Refused, and therefore text -- `#REF!` when used as an arithmetic or aggregate
operand (§8): a leading `+`, exponent notation (`1e3`), a bare `.5` or `5.`,
digit grouping of any kind (`1,000`, `1_000`, `1 000`), a parenthesised negative
(`(500)`), a radix prefix (`0x10`), and `inf`, `nan` and `infinity` in any case."

§4.1's grammar: `number = [ "-" ] 1*DIGIT [ "." 1*DIGIT ]`, with
`DIGIT = %x30-39`, ASCII only.

Each spelling here is one Python's `float()` accepts and the grammar does not.
That is the whole point of the rule: "`\d` in Python, Java and .NET also matches
Arabic-Indic `٥` and thirty other digit families, so a naive implementation reads
`٥` as five while a strict one reads it as text -- the same cell, two totals, no
error."

## Why this one is the arithmetic shape, not the aggregate shape

§4.1.6 says `#REF!` "when used as an **arithmetic** or aggregate operand". The
reference reaches its `number` check only on the aggregate path: `sum(qty)` over
`1e3` correctly yields `#REF!(qty)`, while the identical cell reached through a
computed column `t = qty * unit` raises an uncaught `ValueError`. Two paths, one
guard. §9's opening sentence -- "Recognition is total: every byte sequence has
exactly one defined outcome" -- makes a traceback neither outcome.
