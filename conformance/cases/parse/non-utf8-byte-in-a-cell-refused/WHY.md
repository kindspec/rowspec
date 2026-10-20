The artifact is a well-formed two-column table, except for the cell under
`name` in row `r_1`. It holds `caf` followed by the single byte `0xE9`, which
is `é` in Latin-1. In UTF-8, `0xE9` opens a three-byte sequence, and the
next byte, a space (`0x20`), cannot continue it. The file has no declarations
and no BOM, and every line ends in LF.

The artifact is stored as `input.bin`, not `input.mdtbl`, because its bytes
are not UTF-8, as the case format requires: "A `parse` case may hold its
artifact as `input.bin` instead, and must when the bytes are not UTF-8"
(conformance/cases/README.md, #262).

Nothing else is refused. The bad byte sits in an ordinary data cell, not in
an identifier, so §9.16 does not reach it. The alignment row is valid, both
rows have the header's field count, and no `key` is declared. §9.14 is in any
case decided before any line is classified. A reader that decodes with
replacement characters, or as Latin-1, reads the value `café` or `caf�` and
accepts the file.

## Identifier

This case asserts `refusal: "bad-encoding"`.

§3: "UTF-8, no BOM."

§9.14: "`bad-encoding`: bytes that are not well-formed UTF-8 (§3). A property of the bytes, decided before any line is classified. A leading BOM is §9.26, not this entry"

§9: "A conformance case that names one identifier is therefore a case in which exactly one refusal applies; where several apply, the case names each of them, and reporting any one passes."

## Provenance

Written from SPEC.md at rowspec `1786215` alone, by an author who saw no
implementation. The files read were these, fetched with
`gh api repos/kindspec/rowspec/contents/<path>?ref=<ref>`, by sha256:

    832a8568c6a1f54edb9c930bb806c45ac3077990fcfb6077853fc00f39df4a6e  SPEC.md @ 1786215
    45cfe0b46e181acbb2c2320b6e6be75c05f8ae3881e532435ababf9961553c5c  conformance/cases/README.md @ 1786215
    4074dc00ef8115e923bc69e47726442546fd14003daa6de8e71646c76933a578  conformance/cases-csv/README.md @ 1786215
    96d7c22c6eaeda76b90164adcc1e27e3c78a3cbd543f57db2ec2cc3eb01de4f6  conformance/cases/README.md @ ef28bed9d78fa5668c26d4f92d748fc2be6847d9
