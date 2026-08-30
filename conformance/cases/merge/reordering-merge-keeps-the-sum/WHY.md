# Why this case exists

§7's [CHOICE] paragraph names the mechanism: "A merge reorders rows. So
without this rule a total can change because of a merge that lost no data and
conflicted on nothing." This case is that sentence as a fixture.

The base ledger's huge amounts interleave (`1e308` first, `-1e308` last, small
rows between), so a left-to-right accumulator survives it. `theirs` inserts a
second `1e308` row just under the first; `ours` appends a second `-1e308` row
at the end. Git merges the two edits cleanly — no conflict, no data lost —
and the merged file now has the two positives adjacent at the top, so a
left-to-right accumulator reaches `2e308` and overflows on a table whose exact
sum is `6`. The merge added `+1e308` and `-1e308`, which cancel exactly, so
the base's total of `6` is still the answer; `#REF!(overflow)` here is a total
that changed because rows changed places, which is §1's failure with
arithmetic as the mechanism.

The eval pair (`eval/sum-huge-cancellation-*`) pins the same rule on static
files; this case pins that the reordering arrives by an ordinary clean merge.
