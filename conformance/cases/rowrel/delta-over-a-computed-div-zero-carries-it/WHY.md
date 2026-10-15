# Why this case exists

Ordered by `n`, the computed `c = a / z` is `1` and then `#REF!(/0)`.
§7: "Each operand carries the error it originated, so a computed `c`
holding `#REF!(/0)` here makes `delta(c)` `#REF!(/0)`, not a relabelled
`#REF!(c)`." Only this row gives an error.
