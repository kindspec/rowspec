The sidecar's `key` is JSON `null`. The CSV has no fault.

§13: "A sidecar names a column as §9.2 compares names in this profile: after
trimming ASCII space and tab only, and after NFC. So `" joined"` names the
column `joined`, and `""` names a column whose header cell is empty. A name
that is not a string, or that names no column, is refused, whichever member
holds it: a declaration naming nothing is refused rather than skipped,
because skipping it switches off the check it asked for."

`null` is not a string, so `key` is refused. A reader that treats a `null`
member as absent accepts this file.

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the name not being a string is the only fault in the file and
its sidecar, so a reader that refuses it has refused for that reason or for
one §13 does not give. What the case does not pin is which reason the reader
reports.
