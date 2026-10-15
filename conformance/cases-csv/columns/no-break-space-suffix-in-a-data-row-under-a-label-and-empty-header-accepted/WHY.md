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
sidecar there is no key, so nothing constrains its values.

The outcome does not rest on that reading alone. If the second line were
taken as the names, §13 settles those too: "A leading or trailing non-ASCII
space, such as U+00A0, is part of the name, as it is part of a key value, so
`a` and `a<U+00A0>` are two names". Either way no refusal applies and the
file is accepted. A reader that promotes the second line to a header and
trims U+00A0 refuses it as a duplicate.

The refused twin is
`columns/no-break-space-suffix-in-a-data-row-under-two-empty-names-refused`.
