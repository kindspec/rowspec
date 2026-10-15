The CSV's first header cell is empty; its values `r1` and `r2` are unique.
The sidecar's `key` is the empty string.

§13: "A sidecar names a column as §9.2 compares names in this profile: after
trimming ASCII space and tab only, and after NFC. So `" joined"` names the
column `joined`, and `""` names a column whose header cell is empty. A name
that is not a string, or that names no column, is refused, whichever member
holds it: a declaration naming nothing is refused rather than skipped,
because skipping it switches off the check it asked for."

"`""` names a column whose header cell is empty", and §13 admits an empty
header cell as a column name. So the key names the first column and the file
is accepted. A reader that treats an empty name as no name refuses it.

`sidecar/empty-key-name-names-an-empty-header-cell-applies-refused` shows
the key is in force.
