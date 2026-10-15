# Why this case exists

Group `p` holds 10^400 (a `1` and 400 zeros), whose binary64 value is
infinite, and `1`; group `q` holds `4` and `2`. `lo` and `hi` are per-row
group aggregates over the row's own group (§7, §4.2 rule 5: `@g` is bound to
the row whose cell is being computed).

No `order` is declared, and the file order and the key order (`r_1` to `r_4`)
agree, so `row_index` names the same row under either.

The control for `rowrel/group-min-over-an-infinite-cell-is-overflow`: `lo` in
row `r_4`, group `q`, whose matched rows hold `4` and `2`. §8: "Under a
`where`, "any column" means the rows the predicate MATCHED. A `#REF!`
sitting in a row the predicate excludes does not poison the aggregate". The
infinite cell is in group `p`, so it is never an operand here, and `lo` is
`2`.
