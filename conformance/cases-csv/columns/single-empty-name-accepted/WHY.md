# Why this case exists

Control for `repeated-empty-name-refused` and `two-empty-names-refused`.
The header `,x` has one empty name and one non-empty name.

§13: "column names are exempt from §4.1.9's allowlist ... **and so is an
empty header cell**." One empty name is a valid CSV column name, and with
no second one there is no duplicate for §9.2 to refuse.

This catches the opposite over-correction: a fix that refuses any empty
header cell, or any header that "looks grouped", instead of refusing a
repeated name. Both refusing siblings would still pass under it; this case
would not.
