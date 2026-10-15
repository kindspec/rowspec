The CSV's second header cell is empty, and its column holds two numbers.
`columns` types `""` as `number`.

§13: "A sidecar names a column as §9.2 compares names in this profile: after
trimming ASCII space and tab only, and after NFC. So `" joined"` names the
column `joined`, and `""` names a column whose header cell is empty. A name
that is not a string, or that names no column, is refused, whichever member
holds it: a declaration naming nothing is refused rather than skipped,
because skipping it switches off the check it asked for."

The empty name names the empty-headed column, which holds numbers, so the
file is accepted.
