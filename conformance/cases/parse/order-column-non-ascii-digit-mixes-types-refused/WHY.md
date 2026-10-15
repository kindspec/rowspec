# Why this case exists

The order column `n` holds `10` and `٥`, ARABIC-INDIC DIGIT FIVE (U+0665).

§4.1.6: "A cell is read as a number only if it matches `number`. Refused,
and therefore text — `#REF!` when used as an arithmetic or aggregate
operand (§8): a leading `+`, exponent notation (`1e3`), a bare `.5` or `5.`
…". `DIGIT` "is U+0030–U+0039 and nothing else".

So the second value is text beside a number. §6: `c` "must have a single type across all rows — `number`, `date`
(`Y-M-D` or `Y/M/D`), or `text`. **Mixed types are refused**", and §9.10
(`bad-order-column`) refuses an order column that "mixes types".
