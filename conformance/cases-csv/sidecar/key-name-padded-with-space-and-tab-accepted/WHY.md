The sidecar's `key` is the string `" id<TAB>"`: a space, `id`, a tab. The
CSV's first column is `id` and its values are unique.

§13: "A sidecar names a column as §9.2 compares names in this profile: after
trimming ASCII space and tab only, and after NFC. So `" joined"` names the
column `joined`, and `""` names a column whose header cell is empty. A name
that is not a string, or that names no column, is refused, whichever member
holds it: a declaration naming nothing is refused rather than skipped,
because skipping it switches off the check it asked for."

Trimmed of ASCII space and tab, the name is `id`, which names the first
column, so the file is accepted. A reader that compares the name untrimmed
finds no such column and refuses.

`sidecar/key-name-padded-with-space-and-tab-applies-refused` is the same
sidecar over repeated ids, which shows the key is in force.
