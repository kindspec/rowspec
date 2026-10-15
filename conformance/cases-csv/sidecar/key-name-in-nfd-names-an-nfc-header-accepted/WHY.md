The sidecar's `key` is `café` in NFD (`e` then U+0301 COMBINING ACUTE
ACCENT). The CSV's first header cell is `café` in NFC (U+00E9). Its values
are unique.

§13: "A sidecar names a column as §9.2 compares names in this profile: after
trimming ASCII space and tab only, and after NFC. So `" joined"` names the
column `joined`, and `""` names a column whose header cell is empty. A name
that is not a string, or that names no column, is refused, whichever member
holds it: a declaration naming nothing is refused rather than skipped,
because skipping it switches off the check it asked for."

After NFC the two are equal, so the key names the first column and the file
is accepted. A reader that compares code points without normalising finds no
column and refuses.
