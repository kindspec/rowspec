# Why this case exists

The file is two lines:

    g,
    a,a<U+00A0>

The first line is a label and an empty cell, the shape a spreadsheet's merged
group header exports as. The second holds `a`, and `a` followed by U+00A0
NO-BREAK SPACE.

§13 has one header: it speaks of "a header cell" and "column names", and
nowhere of a header that spans records. So the names are `g` and the empty
name. They are distinct, and a single empty name is accepted
(`columns/no-break-space-name-and-empty-name-accepted` and its siblings).
The second line is a data row with the header's field count, and with no
sidecar there is no key, so nothing constrains its values. No refusal
applies and the file is accepted.

**This is an acceptance control only.** It does not test how U+00A0 is
treated: under `g,` the data row never affects the result, so a reader that
trims U+00A0 from data values, or from names, still accepts this file. Its
job is to show that a header holding one empty name and a data row of
look-alike values is not refused, so that a reader cannot pass the refused
twin, `columns/no-break-space-suffix-in-a-data-row-under-two-empty-names-refused`,
by refusing every file of this shape.
