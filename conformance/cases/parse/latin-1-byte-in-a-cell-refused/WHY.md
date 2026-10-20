# Why this case exists

A valid file in which one cell, `café`, was saved as Latin-1: the `é` is the
single byte `0xE9`, followed by a space. `0xE9` opens a three-byte UTF-8
sequence and `0x20` is not a continuation byte, so the bytes are not
well-formed UTF-8. Every other byte is ASCII.

§9.14, `bad-encoding`: "bytes that are not well-formed UTF-8 (§3). A
property of the bytes, decided before any line is classified. A leading BOM
is §9.26, not this entry". §3: "UTF-8, no BOM."

No case asserted `bad-encoding` after `parse/bom-refused` moved to
`leading-bom` (#222).

The artifact is `input.bin`, not `input.mdtbl`. A runner reads every
`.mdtbl` in the tree as UTF-8 text, so these bytes as `input.mdtbl` would
stop the whole tree rather than fail one case. The `parse` handler reads
`input.bin` as bytes and hands them to the implementation's bytes entry
point (`README.md`, "Shape").

## Why no other §9 entry applies

- §9.18, §9.19 and §9.6 could reach the fourth line only by reading `0xE9`
  as a character of it. §9.14 is "decided before any line is classified",
  and bytes that do not decode are not characters of any line. Even a
  reader that substituted a character for the byte would find a
  well-formed table line of three fields.
- §9.26: the file starts with `|`, not a BOM.
- §9.16: the byte is in `item`, not in a column name, an aggregate name or
  the key column. The key values `r_1` and `r_2` are ASCII `ident`s.
- §9.15: every line ends in LF, and `0xE9` is not `CR`.
- §9.6, §9.7, §9.8, §9.21: the header, the alignment row and the data rows
  have three fields; `---`, `---` and `--:` are `align-cell`s; no data row
  is alignment-style.
- §9.2 to §9.5, §9.11, §9.12: the names are distinct, there is one `key`
  declaration naming the stored column `id`, both declarations match
  `declaration`, and `sum` is known.
- §9.1, §9.13: no marker line, and a table is present.
- §9.9, §9.10, §9.17, §9.20, §9.22 to §9.25: no formula column, no
  computed cell, no `if`, no `order`.

## Provenance

This case was **not** written without the implementation. Its author also
wrote `evaluate_bytes` in both `reference/rowspec/` and
`reference/rowspec_alt/` and the runner path that reads `input.bin`, and
had read both implementations' encoding handling. It lands in a separate
change from that code, per CONTRIBUTING.md, but it is not independent
evidence. The fixture bytes are those of the case first proposed for this
gap on #213 (commit `cd48067`, reverted there because no implementation
took bytes), and the expected identifier rests on §9.14 alone.
