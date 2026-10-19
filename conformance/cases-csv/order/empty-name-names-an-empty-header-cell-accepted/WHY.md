The control for the two other `order/empty-name-*` cases. The header is
`id` and an empty cell; the sidecar's `order` is the empty string and
`key` names `id`.

§13: "A sidecar names a column as §9.2 compares names in this profile:
after trimming ASCII space and tab only, and after NFC. So `" joined"`
names the column `joined`, and `""` names a column whose header cell is
empty. A name that is not a string, or that names no column, is refused,
whichever member holds it: a declaration naming nothing is refused rather
than skipped, because skipping it switches off the check it asked for."

§13: "column names are exempt from §4.1.9's allowlist. [...] so is an
empty header cell."

So `order` names the empty-headed column, which holds `b` and `a`: both
text, neither blank, neither a non-finite spelling. §6: "A row's
position in the file is never an input to any computation", so the
rows need not be written in order. The file is accepted. A reader that
refuses an empty `order` name outright refuses it.
