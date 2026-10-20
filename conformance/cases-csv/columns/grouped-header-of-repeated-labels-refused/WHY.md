# Why this case exists

The file is three lines:

    Europe,Europe,Europe,Asia,Asia,Asia
    France,Germany,Spain,Japan,China,India
    1,2,3,4,5,6

It is the two-row "grouped" header a spreadsheet exports from merged cells:
the first line labels spans of columns, and the line below holds six
distinct names.

§13 says which line is the header: "The header is the first record that
does not start on a conflict line". No line here starts on one, so the
header is the first line, and its six cells are the column names. The
second line is a data row, and nothing in §13 or §9 lets it name the
columns instead.

§13: "names still compare after NFC, so §9.2 refuses two that normalise
alike." `Europe` appears three times and `Asia` three times, so the header
has two column names that compare alike, twice over, and §9.2
(`duplicate-column`) refuses the file.

Exactly one refusal applies: there is no sidecar, so no key and no §9.5;
every record has six fields like the header, so §9.6 is satisfied; the
bytes are ASCII with LF endings, and no name holds a `Cf` character.

The failure this pins is an implementation that recognises the grouped
shape and reports it under some other identifier, or none: however the
shape is described, the refusal is a duplicate column name.

Siblings: `repeated-empty-name-refused` (the grouped shape with an empty
label, `,x,,,,`) and `duplicate-column-refused` (one repeated name).

This case was added from the code's coverage gap, not blind: its author
had read `reference/rowspec/csvmode.py`, which has a separate path for this
shape that no other case reached.

## Identifier

This case asserts `refusal: "duplicate-column"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "two column names that compare alike, two empty header cells included: §9.2 `duplicate-column`."

§9.2: "`duplicate-column`: a duplicate column name"
