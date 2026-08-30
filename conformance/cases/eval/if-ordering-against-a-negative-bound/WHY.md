# Why this case exists

`signed = [ "-" *WSP ] literal`. Parsing a negative bound is not the same as
*meaning* one, and `parse/if-comparison-rhs-negative-literal-accepted` can only
assert the first. This case asserts the second, and the row values are chosen so
that the two ways of getting it wrong both produce a different total from the
right one:

| `a`    | `a > -1` (correct) | minus dropped: `a > 1` | minus moved: `-a > 1` |
| ------ | ------------------ | ---------------------- | --------------------- |
| `-5`   | 0                  | 0                      | 1                     |
| `-0.5` | 1                  | 0                      | 0                     |
| `3`    | 1                  | 1                      | 0                     |
| total  | **2**              | 1                      | 1                     |

`-0.5` is the row that separates them, and it exists because the interesting
part of a negative bound is the interval between it and zero — the values a
guard written `> -1` is there to admit and a guard written `> 1` is not.

"Minus moved to the left" is not a strawman: `factor = [ "-" *WSP ] primary`
already puts an optional minus in front of an operand, and a parser that reaches
`order-rhs` by calling its `factor` routine — the one-line implementation — is
correct here by accident and wrong at `parse/if-comparison-rhs-negated-ident-refused`.

`y` is the same comparison written `- 1`, which `signed`'s `*WSP` admits: the
minus is part of the bound, not an operator with an operand, so the space
changes nothing. Both totals must be `2`. An implementation that lexes `-` and
`1` as one token refuses `y`; one that treats the space as significant gives it
a different value from `x`, and the case asserts they agree.
