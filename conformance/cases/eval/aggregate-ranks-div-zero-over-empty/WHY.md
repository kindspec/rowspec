# Why this case exists

The table has two rows, `r_1` with `k` = 1 and `v` = 5, and `r_2` with `k` = 2
and a blank `v`. Each intermediate value, from SPEC.md:

- `e = min(v where k = @k)` is a per-row group aggregate, with `@k` "bound
  **once, to the row whose cell is being computed**" (§4.2 rule 5). In `r_2`
  the group `k` = `2` matches `r_2` alone, whose `v` is blank. §7: "**A blank
  cell is skipped by `sum`, `min`, `max` and `avg`**", and "`min`, `max` and
  `avg` of nothing are `#REF!(empty)`"; "Three routes reach it ... a column
  whose every cell is blank". So `e` is `#REF!(empty)` in `r_2`. (In `r_1` it
  is 5, and nothing reads it there.)
- `x = if(k = 1, 1 / 0, e)`. §4.2 rule 10: "A `literal` right-hand side
  compares numbers", and "**Only the selected branch is evaluated.**" In `r_1`
  `k` is 1, the branch `1 / 0` is selected, and §4.2 rule 2 says "**Division by
  zero evaluates to `#REF!(/0)`**"; §8 adds that "an operation on literals,
  such as `1 / 0`, is evaluated per row like any other". So `x` is `#REF!(/0)`
  in `r_1`. In `r_2` `k` is 2, the branch `e` is selected, and `x` carries
  `e`'s error unchanged (§8, "carries the *originating* name", "Errors
  propagate"): `#REF!(empty)`.
- `s := sum(x)`. Its operands hold two different errors, `#REF!(/0)` and
  `#REF!(empty)`. §8: "**When its operands hold several different `#REF!`
  values, an aggregate carries the one whose shape ranks first: `cycle`, then a
  name, then `/0`, then `empty`, then `overflow`.**" `/0` ranks before `empty`,
  so `s` is `#REF!(/0)`.

§8 continues: "Never the first by row, in the file or in the declared order".
This case and its twin hold the same rows with the two data lines swapped
(§6: "Shuffling every line leaves all values unchanged"), so a reader that
takes the first error by row passes at most one of them.

The tree's other ranking cases put `/0` and `empty` each against `overflow`
(`eval/aggregate-ranks-div-zero-over-overflow`,
`eval/aggregate-ranks-empty-over-overflow`); this pair puts them against each
other.

The twin is `eval/aggregate-ranks-div-zero-over-empty-swapped`.
