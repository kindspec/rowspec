The CSV's first header cell is two spaces; its values are unique. The
sidecar's `key` is a single tab.

§13: "A sidecar names a column as §9.2 compares names in this profile: after
trimming ASCII space and tab only, and after NFC. So `" joined"` names the
column `joined`, and `""` names a column whose header cell is empty. A name
that is not a string, or that names no column, is refused, whichever member
holds it: a declaration naming nothing is refused rather than skipped,
because skipping it switches off the check it asked for."

§13, on column names: "A name is trimmed of ASCII space and tab only before
§9.2 compares it, as a key value is (§4.1.4): `a` with spaces or tabs around
it and `a` are one name, and so are a header cell of spaces, one of a tab
and an empty one".

The header cell of spaces trims to the empty name, and so does the tab, so
the key names the first column and the file is accepted.
