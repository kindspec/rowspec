# Why this case exists

The third table line is `| :-: | --- |`, a data row each of whose cells is
an `align-cell`. The table declares no key and has no computed column.

§9.8, `alignment-row-in-data`: "an alignment-style row among the data rows
— a data row *every* cell of which is an `align-cell` (§4.1.5)". §4.1.5:
"A *data* row is alignment-style (§9.8) if and only if **every** one of its
cells matches `align-cell`".

`parse/dashed-data-row` names this identifier beside `bad-identifier` and
`value-in-computed-cell`: its dashed row puts `---` in the key column and
in a computed column. This case removes both: with no `key :=` there is no
key column, and with no `=` in the header there is no computed column.

## Why no other §9 entry applies

- §9.16 `bad-identifier` covers "a value of the key column". No key is
  declared, so no column is the key column, and `:-:` in `item` is an
  ordinary text value. No `order` is declared, so §9.25 does not require a
  key.
- §9.17 `value-in-computed-cell`: neither `item` nor `qty` has a formula.
- §9.21 `bad-alignment-row` is about the table's **second** line, which is
  `| --- | --: |`, a valid alignment row. §9.7: it has two fields, as the
  header does.
- §9.6: every data row has two fields.
- §9.18, §9.19: every table line has a leading and a closing `|`, the
  table is one contiguous run, and the other lines are a blank and one
  declaration.
- §9.12: `n := count(item)` matches `declaration`. §9.11: `count` is known.
  It is `count` rather than `sum` only so that no aggregate reads `---` as
  an operand; that would be a `#REF!` value under §8, not a refusal, either
  way.
- §9.2, §9.3: `item`, `qty` and `n` are distinct `ident`s. §9.4, §9.5: no
  `key` or `order` declaration.
- §9.1, §9.13, §9.14, §9.15, §9.26: no marker line, a table is present,
  the file is ASCII with LF endings and no BOM.
- §9.9, §9.10, §9.20, §9.22–§9.24: no formula, no `if`, no `order`.
