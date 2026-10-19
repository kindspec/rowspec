# Why this case exists

A valid file in which one cell, `café`, was saved as Latin-1: the `é` is the
single byte `0xE9`, followed by a space. `0xE9` opens a three-byte UTF-8
sequence and `0x20` is not a continuation byte, so the bytes are not
well-formed UTF-8. Every other byte is ASCII.

The artifact is `input.bin`, not `input.mdtbl`. kindkit decodes every
`.mdtbl` fixture as UTF-8 before a handler runs, so these bytes as
`input.mdtbl` would be a fault in the whole tree rather than a case. The
`parse` handler in `conformance/run_cases.py` reads `input.bin` itself and
hands the implementation the bytes undecoded.

§9.14, `bad-encoding`: "bytes that are not well-formed UTF-8 (§3). A
property of the bytes, decided before any line is classified. A leading BOM
is §9.26, not this entry". §3: "UTF-8, no BOM."

No case asserted `bad-encoding` once `parse/bom-refused` moved to
`leading-bom`.

## Why no other §9 entry applies

- §9.18, §9.19 and §9.6 could only reach the fourth line by reading `0xE9`
  as a character of it. §9.14 is "decided before any line is classified",
  and §9.26 draws the consequence for the BOM: "Like §9.14 it is a property
  of the bytes, decided before any line is classified, so it is never also
  a character of line 1." Bytes that do not decode are not characters of
  any line either. The byte is in a non-key text cell, so even a reader
  that substituted a character for it would find the line a well-formed
  table line of three fields.
- §9.26: the file starts with `|`, not a BOM.
- §9.16: the byte is in `item`, not in a column name, an aggregate name or
  the key column. The key values `r_1` and `r_2` are ASCII `ident`s.
- §9.15: every line ends in LF, and `0xE9` is not `CR`.
- §9.6, §9.7, §9.8, §9.21: header, alignment row and data rows have three
  fields; `---`, `---`, `--:` are `align-cell`s; no data row is
  alignment-style.
- §9.2–§9.5, §9.12, §9.11: names are distinct, there is one `key`
  declaration naming the stored column `id`, both declarations match
  `declaration`, and `sum` is known.
- §9.1, §9.13: no marker line, and a table is present.
- §9.9, §9.10, §9.17, §9.20, §9.22–§9.25: no formula, no computed column,
  no `if`, no `order`.
