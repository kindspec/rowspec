# Why this case exists

The sidecar declares `id` the key. The key values are `r1` and `r1` padded
with horizontal tabs.

§13: the values of a declared key are checked "after trimming ASCII space
and tab only (§4.1.4)", and §4.1.4: "a row keyed `r_01` and a row keyed
`<tab>r_01` must be one duplicate (§9.5)". Both values trim to `r1`, so the
file is refused under §9.5, which §13 applies with a sidecar.
