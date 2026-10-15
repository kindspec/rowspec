The sidecar's `key` is `" id<TAB>"`, and the CSV repeats the id `r1`.

§13: "A sidecar names a column as §9.2 compares names in this profile: after
trimming ASCII space and tab only, and after NFC. So `" joined"` names the
column `joined`, and `""` names a column whose header cell is empty. A name
that is not a string, or that names no column, is refused, whichever member
holds it: a declaration naming nothing is refused rather than skipped,
because skipping it switches off the check it asked for."

The name trims to `id`, so `id` is the declared key, and §9.5
(`duplicate-row-id`) refuses the repeated `r1`.

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the duplicate row id is the only fault in the file and its
sidecar, so a reader that refuses it has refused for that reason or for one
§13 does not give. What the case does not pin is which reason the reader
reports. On its own the refusal cannot tell a duplicate from a name found to
name no column; `sidecar/key-name-padded-with-space-and-tab-accepted` makes
that distinction, and this case adds that the padded key is applied, not
merely tolerated.
