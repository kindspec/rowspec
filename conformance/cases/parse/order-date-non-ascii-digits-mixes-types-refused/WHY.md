# Why this case exists

The order column `d` holds `2024-01-05` and a date whose year is written in
Arabic-Indic digits (U+0662 U+0660 U+0662 U+0664).

§4.1.7: "A cell is a date only if it matches `date`", and §4.1's `date` is
built from `DIGIT = %x30-39`, ASCII only. The second value does not match
`date` or `number`, so it is text beside a date. §6: `c` "must have a single type across all rows — `number`, `date`
(`Y-M-D` or `Y/M/D`), or `text`. **Mixed types are refused**", and §9.10
(`bad-order-column`) refuses an order column that "mixes types".
