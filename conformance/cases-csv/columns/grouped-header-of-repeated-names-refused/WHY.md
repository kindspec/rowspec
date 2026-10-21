The header is the grouped shape a spreadsheet export produces when a merged
cell spans several columns: `Europe,Europe,Europe,Asia,Asia,Asia`. Under it,
one row of distinct names: `France,Germany,Italy,China,India,Japan`. There is
no sidecar.

The header holds two names three times each. §13 exempts a CSV column name
from §4.1.9's allowlist, but not from §9.2, and nothing in §13 exempts a
grouped header from §9.2 or treats its first row as anything but the header.
A reader that takes the second row as the header, or folds a run of equal
names into one group, accepts this file.

Nothing else is refused. The names hold no `Cf` character, the row has the
header's six fields, and with no sidecar there is no declared key.

## Identifier

This case asserts `refusal: "duplicate-column"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "two column names that compare alike, two empty header cells included: §9.2 `duplicate-column`."

§13: "Only a `Cf` format character in a column name is still refused, and names still compare after NFC, so §9.2 refuses two that normalise alike."

§9.2: "`duplicate-column`: a duplicate column name"

## Provenance

Written from SPEC.md at rowspec `1786215` alone, by an author who saw no
implementation. The files read were these, fetched with
`gh api repos/kindspec/rowspec/contents/<path>?ref=<ref>`, by sha256:

    832a8568c6a1f54edb9c930bb806c45ac3077990fcfb6077853fc00f39df4a6e  SPEC.md @ 1786215
    45cfe0b46e181acbb2c2320b6e6be75c05f8ae3881e532435ababf9961553c5c  conformance/cases/README.md @ 1786215
    4074dc00ef8115e923bc69e47726442546fd14003daa6de8e71646c76933a578  conformance/cases-csv/README.md @ 1786215
    96d7c22c6eaeda76b90164adcc1e27e3c78a3cbd543f57db2ec2cc3eb01de4f6  conformance/cases/README.md @ ef28bed9d78fa5668c26d4f92d748fc2be6847d9
