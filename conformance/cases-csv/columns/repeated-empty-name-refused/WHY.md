# Why this case exists

The header row is `,x,,,,`: six column names, five of them the empty
string. It is the shape of a two-row "grouped" header, where the first row
labels a span of columns and the real names are on the row below.

§13 decides it in two sentences. "**column names are exempt from §4.1.9's
allowlist** ... so `first name`, `total (USD)` and `a-b` are column names,
**and so is an empty header cell**." And: "names still compare after NFC,
so §9.2 refuses two that normalise alike." The empty string is a column
name, it appears five times, and §9.2 (`duplicate-column`) refuses a
duplicate column name. Nothing in §13 or §9 gives a CSV a grouped header,
so the row is read as what it is, a row of column names.

Exactly one refusal applies: there is no sidecar, so no key and no §9.5;
the data row has six fields like the header, so §9.6 is satisfied; the
bytes are ASCII with LF endings.

The failure this pins is an implementation that leaves the empty string out
of duplicate detection, because it looks like "no name" rather than a name.
The file must be refused, and refused, not crashed on: §9's "every byte
sequence has exactly one defined outcome".

Siblings: `two-empty-names-refused` (the same rule without the grouped
shape) and `single-empty-name-accepted` (one empty name is not a
duplicate).

## Identifier

This case asserts `refusal: "duplicate-column"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "two column names that compare alike, two empty header cells included: §9.2 `duplicate-column`."

§9.2: "`duplicate-column`: a duplicate column name"
