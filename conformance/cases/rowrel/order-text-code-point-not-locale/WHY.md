# Why this case exists

SPEC.md §4.1.8: "A `text` order column (§6), and the row-key tiebreak of §6's
sort tuple, compare by **Unicode code point** over the NFC-normalised, trimmed
value. Locale collation is refused, not merely not required: it makes the
interpretation of an artifact a function of the reading machine's locale and ICU
version rather than of the artifact's bytes, so the same commit yields two row
orders -- and under `cumulative` two sets of numbers -- on two developers'
machines, with no diagnostic on either."

Code point order is `Apple` (U+0041), `Zebra` (U+005A), `apple` (U+0061),
`Ápple` (U+00C1): running total 10, -10, -5, 95, so `lo` is -10.

A locale collator orders these `apple`, `Apple`, `Ápple`, `Zebra` -- running
total 5, 15, 115, 95, so `lo` is 5.0 and `hi` is 115.0. The amounts are chosen
so that both the minimum and the maximum differ; a table of positive amounts
would hide the defect behind an identical total.
