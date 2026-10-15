The mirror of `sidecar/key-name-in-nfd-names-an-nfc-header-accepted`: the
sidecar's `key` is `café` in NFC and the CSV's first header cell is `café`
in NFD. Its values are unique.

§13: "A sidecar names a column as §9.2 compares names in this profile: after
trimming ASCII space and tab only, and after NFC. So `" joined"` names the
column `joined`, and `""` names a column whose header cell is empty. A name
that is not a string, or that names no column, is refused, whichever member
holds it: a declaration naming nothing is refused rather than skipped,
because skipping it switches off the check it asked for."

Both sides are normalised before they are compared, so the key names the
column and the file is accepted. A reader that normalises only the sidecar
name, or only the header, refuses one of the pair.
