The sidecar's `order` is `" o "`, a space either side. The CSV's column is
`o`, holding three numbers.

§13: "A sidecar names a column as §9.2 compares names in this profile: after
trimming ASCII space and tab only, and after NFC. So `" joined"` names the
column `joined`, and `""` names a column whose header cell is empty. A name
that is not a string, or that names no column, is refused, whichever member
holds it: a declaration naming nothing is refused rather than skipped,
because skipping it switches off the check it asked for."

The name trims to `o`, which names the column, so the file is accepted.
