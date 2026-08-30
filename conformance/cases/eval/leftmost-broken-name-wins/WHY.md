# Why this case exists

§8: "**Which `#REF!` a formula carries, when more than one applies, is decided
by POSITION IN THE FORMULA TEXT: the leftmost.**"

Neither `zz_gone` nor `aa_gone` exists, and the names are chosen so that the
textual order and the alphabetical order disagree: alphabetically `aa_gone`
comes first, textually `zz_gone` does. An implementation that collects broken
names into a sorted set — the natural shape when a resolver reports all its
misses at once — answers `#REF!(aa_gone)` and passes any case whose names
happen to be in alphabetical order already. `sx` pins the textual answer.

`sy` pins the other half of §8's argument: the name must not come from
*evaluation* order either, because §4.2 rule 9 makes evaluation strategy a
free choice and a value that `expect.json` asserts on must not leak it. A lazy
`if` that resolves only the branch a row selects reports `zz_gone` on `r_01`
and `aa_gone` on `r_02`, and which of those poisons `sy` then depends on which
row the aggregate happened to visit first. §4.2 rule 10 makes name resolution
a property of the header — the same for every row — and §8 picks the leftmost
of the formula's broken names: `#REF!(zz_gone)` in both rows, whatever branch
either row selects.
