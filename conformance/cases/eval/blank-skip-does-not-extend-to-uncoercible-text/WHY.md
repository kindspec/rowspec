# Why this case exists

SPEC §7 draws the line in two sentences that must hold in the same column at
once: "The other four coerce, so for them a **non-blank** value that will not
parse as a number is `#REF!` under §8, and one such cell poisons the aggregate
rather than being skipped" — and "A blank cell is skipped."

`eval/ref-poisons-every-aggregate` has the uncoercible cell with no blank in
sight, and the skip cases have blanks with nothing uncoercible. An
implementation that generalises the skip rule to "skip anything that isn't a
number" passes both families: here it reports `5` for `mn`, `mx` and `av` — a
plausible number in every cell — where the truth is `#REF!(amt)`. The blank
and the `1,000` must sit in one column for that misreading to have something
to fail against.

`n` stays `3`: `count` never coerces, so neither the blank nor the text
poisons it.
