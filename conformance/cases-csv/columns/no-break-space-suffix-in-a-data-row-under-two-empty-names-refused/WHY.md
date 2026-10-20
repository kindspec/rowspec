# Why this case exists

The file is two lines:

    ,
    a,a<U+00A0>

The first line is two empty header cells. The second holds `a`, and `a`
followed by U+00A0 NO-BREAK SPACE.

§13: "`a` with spaces or tabs around it and `a` are one name, and so are a
header cell of spaces, one of a tab and an empty one, so any two of them are a
duplicate." The two empty names are a duplicate, and §9.2
(`duplicate-column`) refuses the file.

§13 has one header — it speaks of "a header cell" and "column names", and
nowhere of a header spanning records — so the second line is data and does
not rescue the first. A reader that treats an all-empty first line as a group
row and takes its names from the second line sees `a` and `a<U+00A0>`, which
§13 makes two names, and accepts the file. This case goes red for that
reader.

No sidecar is supplied and both lines have two fields, so §9.2 is the only
refusal SPEC.md gives this file. The CSV tree asserts only that a file is
refused, never which refusal (§13: "its conformance cases assert only that a
file is refused"), so this case does not prove §9.2 is the one that fired: a
reader that refused it for another reason would pass too.

The accepted twin is
`columns/no-break-space-suffix-in-a-data-row-under-a-label-and-empty-header-accepted`.

## Identifier

This case asserts `refusal: "duplicate-column"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "two column names that compare alike, two empty header cells included: §9.2 `duplicate-column`."

§9.2: "`duplicate-column`: a duplicate column name"
