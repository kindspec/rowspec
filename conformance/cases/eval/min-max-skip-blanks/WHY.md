# Why this case exists

SPEC §7: "**A blank cell is skipped by `sum`, `min`, `max` and `avg`**, and
contributes nothing rather than poisoning." `eval/sum-skips-blanks` pins the
rule for `sum`; nothing pinned it for `min` and `max`.

Two columns, one positive and one negative, because each extremum is blind on
one side. An implementation that coerces a blank to `0` reports `min(up) = 0`
and `max(down) = 0` — but its `max(up)` and `min(down)` are correct, so a case
with only positive values would let `max` pass on the substitution `sum`
already forbids ("`0` is not substituted"). The mirrored column closes that
half. An implementation that poisons on the blank instead fails all four with
`#REF!`.
