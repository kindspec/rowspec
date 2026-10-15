# Why this case exists

Group `p` holds 10^400 (a `1` and 400 zeros), whose binary64 value is
infinite, and `1`; group `q` holds `4` and `2`. `lo` and `hi` are per-row
group aggregates over the row's own group (§7, §4.2 rule 5: `@g` is bound to
the row whose cell is being computed).

No `order` is declared, and the file order and the key order (`r_1` to `r_4`)
agree, so `row_index` names the same row under either.

This case asserts `lo` in row `r_2`, whose own `a` is the finite `1`. Its
group's matched rows are `r_1` and `r_2`, so its operands are the infinite
cell and `1`. `min` coerces (§7), the infinite cell is `#REF!(overflow)` as an
operand (§8), and "An aggregate poisoned by a `#REF!` among its operands
carries THAT error, unchanged" (§8). So `lo` is `#REF!(overflow)` here, not
`1`. Asserting the row with a finite value of its own shows the error comes
from the group, not from the row.
`rowrel/group-min-without-an-infinite-cell-is-a-number` is the other group.
