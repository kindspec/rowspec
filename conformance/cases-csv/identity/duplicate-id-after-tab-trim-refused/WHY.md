# Why this case exists

The sidecar declares `id` the key. The key values are `r1` and `r1` padded
with horizontal tabs.

§13: the values of a declared key are checked "after trimming ASCII space
and tab only (§4.1.4)", and §4.1.4: "a row keyed `r_01` and a row keyed
`<tab>r_01` must be one duplicate (§9.5)". Both values trim to `r1`, so the
file is refused under §9.5, which §13 applies with a sidecar.

## Identifier

This case asserts `refusal: "duplicate-row-id"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "two rows with one value of the declared key: §9.5 `duplicate-row-id`."

§9.5: "`duplicate-row-id`: a duplicate row id, where a key is declared"
