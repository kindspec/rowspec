<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# The editing API — design

`rowspec.edit` changes a `.mdtbl` file for a program, so that a tool or an
agent never has to edit table text by hand. It is designed around one
property first and its function signatures second: **every edit produces the
smallest text diff the format allows**, because the diff is what git merges.

## Why the diff shape is the design

Git merges by line, and measured on git 2.47 the rule it applies is narrower
than "different lines merge": **two changes merge cleanly only when at least
one unchanged line separates them.** Editing row `b` on one branch and row `c`
on the other, where `c` directly follows `b`, conflicts. So does an insertion
directly after `b` against an edit of `b` or of the row after it, and so do two
insertions at the same place, appending at the end of the table included.

An edit API cannot remove that rule, but it decides how many lines each
operation touches, and therefore how often two edits come within one line of
each other. A writer that re-renders the whole file touches every line, and
conflicts with every concurrent change. SPEC.md §10 measured the same effect
for alignment padding: a widened cell that reflows every row turns two
disjoint edits into a conflict.

## Diff-shape rules

1. **Touch only the lines the operation is about.** No operation re-renders,
   re-aligns or canonicalises a line it was not asked to change. Padding,
   alignment-row spellings, annotations, blank lines and declaration order of
   every other line stay byte for byte as they were.
2. **Keep each line's own terminator.** A changed line keeps its `LF` or
   `CRLF`. A new line takes the terminator of the line it follows, or the
   file's first terminator when that line has none.
3. **Within a changed line, change only the cell or span concerned.** A
   renamed column rewrites the name and the formula spans that name it, and
   leaves the other cells of the header line as they were. A replaced cell
   keeps its padding, and keeps its width when the new text fits.
4. **Never reflow.** In a padded table, a value wider than its column is
   written wider, and the table's alignment is broken for that line, rather
   than every line being re-padded. A new row or column in a padded table is
   padded to the existing widths where it fits, which costs no extra lines.
5. **A file's lack of a final terminator is kept** (§4.1.1). Appending after
   a last line that has none adds one to it, so that the new line is the one
   without: one changed line and one added. Removing a last line that has
   none takes the terminator off the line before it, with one exception: when
   that line is blank it is kept whole, since a blank line without its
   terminator is no line at all, and the file then ends in a terminator.

The resulting shapes, for a table of `N` data rows:

| operation | lines changed |
| --- | --- |
| `insert_row` | 1 added |
| `delete_row` | 1 removed |
| `add_column` | `N + 2` changed: header, alignment row, every data row |
| `delete_column` | `N + 2` changed |
| `rename_column` | 1 (the header) plus 1 per declaration naming it |
| `set_formula` | 1 (the header) |
| `set_declaration` | 1 changed, or 1 added for a new name |
| `delete_declaration` | 1 removed |

`add_column` and `delete_column` are wide because §9.6 requires every data row
to have the header's field count, so every row has to gain or lose a cell. No
writer can do better within the format, and a column change on one branch
therefore conflicts with any row change on another. That conflict is the
format working: a row added on the other branch with the old field count
would otherwise be refused.

## API shape

Every operation is a pure function from text to text:

```python
from rowspec import edit

text, rid = edit.insert_row(text, {"item": "bolt", "qty": "4"}, after="r_0007")
text = edit.delete_row(text, "r_0003")
text = edit.add_column(text, "unit", after="qty")
text = edit.add_column(text, "total", formula="qty * unit")
text = edit.rename_column(text, "qty", "quantity")
text = edit.set_formula(text, "total", "quantity * unit * 1.2")
text = edit.delete_column(text, "unit")
text = edit.set_declaration(text, "grand", "sum(total)")
text = edit.delete_declaration(text, "grand")
```

- A function reads nothing and writes nothing. The caller reads the file with
  `newline=""` so terminators survive, and writes the result back. A refused
  edit raises before the caller has anything to write.
- **Rows are named by key, columns by name, and declarations by name.** There
  are no indices: SPEC.md's rule against coordinates applies to an editing
  interface as much as to the grammar, because an index computed before a
  concurrent change points at the wrong row after it.
- **Position is `after=` or `before=` a key (rows) or a column name (columns),
  or the end.** A row's position is never an input to a value (§6), so
  position is only about the diff: it decides which gap the new line lands
  in, and so which concurrent edits it can collide with. For columns, no
  position means the end. For `insert_row`, the end is `end=True`, and no
  position means the default below. There is no operation that moves a row:
  see "Measured limits".
- **By default a new row goes where its key sorts.** When the rows are
  already in key order, compared by code point, `insert_row` with no
  position puts the row before the first row whose key sorts after its own;
  otherwise it appends at the end. This is a convention of this writer,
  chosen for merge behaviour, and not a rule of the format: SPEC.md says
  nothing about row order in the file, and a table in any order stays valid.
  A generated id is random, so two rows added on two branches land in
  different gaps. Measured by `uv run python tests/test_edit_merge.py` on a
  table of 50 rows in key order, 100 pairs of concurrent inserts with random
  ids of the generated shape:

  | placement | clean | conflict |
  | --- | --- | --- |
  | at the end | 0 | 100 |
  | where the key sorts | 97 | 3 |

  The three conflicts are pairs whose keys sort into the same gap.
- `insert_row` takes the id as `id=`. Without one it generates `r_` followed
  by six hex digits, as `rowspec add-row` does, and returns the id it used.
  Without a declared `key` there is no id, and only the end position is
  available.
- `rename_column` renames the column in the header, in every formula and in
  every declaration that names it, and nowhere else: a string literal, a
  function name, a numeric literal and an annotation are left alone.
- `set_formula` replaces the formula of a computed column. It does not turn a
  stored column into a computed one, since that would empty every data cell.
- `set_declaration` replaces an existing declaration's right-hand side in
  place, keeping its spacing and any inline annotation, or appends a new one
  after the last declaration. `key` and `order` are set the same way.

## Refusal rules

An edit is refused, with nothing returned, in four ways:

1. **The input is refused.** A file SPEC.md refuses is not edited. The
   refusal is the input's own, with its §9 identifier.
2. **The request cannot be written.** These are refused before any text is
   built, and carry an API reason rather than a §9 identifier:
   - `no-such-row`, `no-such-column`, `no-such-declaration`;
   - `no-key`: an id, or a position relative to a key, on a table with no key;
   - `bad-position`: more than one of `after=`, `before=` and `end=True`;
   - `conflicting-id`: an `id=` that differs from the key column's entry in
     the values;
   - `line-break`: CR or LF in a value, formula or declaration (§4.1);
   - `not-representable`: a value with leading or trailing space or tab,
     which the cell would trim away (§4.1.4), or a declaration that would be
     cut short at an inline annotation (§4.1.10);
   - `stored-column`: `set_formula` on a stored column;
   - `last-column`: deleting the only column;
   - `column-referenced`: deleting a column that a formula or declaration
     names. The message names each of them;
   - `rename-captures-reference`: renaming onto a name that a formula or
     declaration already names, as a reference to no column, which would
     silently bind it to the renamed one;
   - `rename-changes-values`: renaming onto a name spelled like a number where
     the column is used as an operand, which would then read as that number
     (§4.2 rule 7).
3. **The result is refused.** The new text is evaluated in full, so every §9
   refusal applies to it: a duplicate id, a bad identifier, a duplicate column
   (renaming onto an existing name), a value in a computed cell, a malformed
   formula or declaration, an alignment-style row. The error carries that
   refusal's §9 identifier.
4. **The result does not say what was asked.** As a last check, a new row,
   header cell, formula or declaration is read back and compared with what
   was requested, and a rename is checked twice: every reference must name
   what it named before, under the new name, and the table must evaluate to
   the same values. A mismatch is refused as `not-representable` or
   `rename-changes-values`. The check exists so that a gap in the rules above
   is a refusal rather than a wrong file.

Values, names and formulas are NFC-normalised before they are written (§3),
and a `|` in a value or formula is written as `\|` (§4.1.3). Bytes the edit
does not change are kept even when they are not NFC, with one exception: a
line that `rename_column` changes is written in NFC as a whole, because the
names it finds are compared in NFC.

Errors are `rowspec.Malformed`, whose `refusal` attribute is the §9
identifier when there is one. `rowspec.edit.EditRefused` is the subclass for
the API's own reasons, with the reason in `reason`.

## What still collides

The diff shape decides which pairs of edits git can merge, and
`tests/test_edit_merge.py` pins the outcome of each pairing it measures
through real merges. In summary, with stock git:

- Edits to rows with at least one untouched row between them merge cleanly,
  and so do inserts into different gaps. Two inserts into the same gap
  conflict, and **appending at the end is one gap**, so two concurrent
  appends always conflict. That is why rows go where their key sorts by
  default (above).
- An insert after row `K` conflicts with an edit of `K` or of the row after
  it, and an edit or delete of a row conflicts with an edit of its neighbour.
- A rename merges cleanly with any row edit, insertion or deletion. It
  conflicts with any other change to the header line, which holds every
  column name and formula (§5), and with a change to a declaration that
  names the renamed column.
- A column added or deleted conflicts with every concurrent row change.
- Two edits to adjacent declaration lines conflict, and so do two new
  declarations, which both append after the last one.
- A clean merge can still name a column the other branch renamed or deleted,
  for example a new declaration `sum(qty)` beside a rename of `qty`. The
  merged file evaluates to `#REF!(qty)`, which `rowspec eval` reports. No
  pairing in the test produces a clean merge to a different number.

## Measured limits

**There is no `move_row`, because a moved row can come back after a delete.**
A move is a deletion and an insertion of the same line. Moving `r_06` to the
top on one branch while the other branch deletes `r_06` merges cleanly in
stock git: the deletion removes the old line and the insertion survives, so
the merged table still has `r_06`, which applying the two edits in either
order would not give. The same happens with the move on either side and the
row moved to the end. No `#REF!` and no refusal says so. A row's position is
never an input to a value (§6), so a move gains nothing but appearance, and
it is not offered.

**Edits to adjacent lines conflict, and the format cannot change that.**
Git's merge treats two changes as overlapping unless an unchanged line lies
between them. A row edit beside an edit of the next row, an insertion beside
an edited row, and two edits of consecutive declarations all conflict, though
none touches the other's line. The table is one contiguous run of lines
(§4.1.2), so a writer cannot put a spacer line between rows, and the API can
only keep its own edits as small as possible.

**Considered and declined: a blank line between declarations.** The grammar
allows blank lines among declarations, and with one between them, replacing
`grand` on one branch and the adjacent `eu` on the other merged cleanly where
it conflicts without. It was declined because that is the only pairing it
helps: two new declarations still both append after the last one and still
conflict, and the convention would cost a second line on every new
declaration.

## What the API does not change

The API adds functions. It does not change SPEC.md, the canonical form, the
grammar, or any existing function; `set_cell` is unchanged.
