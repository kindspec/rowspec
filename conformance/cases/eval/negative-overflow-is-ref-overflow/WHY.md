# Why this case exists

§4.2 rule 2: "**Overflow is `#REF!(overflow)`.** An operation whose IEEE result
is an infinity does not store one. The reasoning is rule 2's below, unchanged:
`inf` is not a `number` under §4.1.6, so a file that stored one could not be
re-read by the implementation that wrote it, and `canon` would not round-trip
its own output."

Two cells of 1e200, written as plain digits because `1e200` is an `ident` and
not a number (§4.1.6), multiply to a binary64 infinity. The answer is the error
value, and it is one of §8's shapes rather than a fourth.

`rowspec_alt` returns `inf` — the exact outcome the rule forbids, and one that
is worse than loud: `sum` over that column is a finite-looking `inf` that
`canon` would then write into a cell no reader, including its own, can read
back as a number.

The negative direction, which returns `-inf` on `rowspec_alt`.
