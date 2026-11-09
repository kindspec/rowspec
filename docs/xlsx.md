<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Export to xlsx, only if you ask for it

```sh
pip install rowspec           # no xlsx dependency, and none is coming
pip install 'rowspec[xlsx]'   # openpyxl, and the exporter that uses it
python -m rowspec_xlsx table.mdtbl table.xlsx            # formulas, the default
python -m rowspec_xlsx --values table.mdtbl table.xlsx   # rowspec eval's values
```

The exporter lives in `export/`, **outside `reference/`**, and that is the
whole design. `reference/` is standard-library-only because a dependency there
is a dependency every independent implementation of the format inherits, and an
independent implementation of a table format must not be required to read xlsx.
A test fails if anything under `reference/` ever imports outside the standard
library, so the boundary is a check rather than a convention.

It writes one sheet holding a spreadsheet table named `rowspec`, with the
declared aggregates below the grid. In both modes every number cell, stored or
computed, is saved with all the digits its binary64 value needs
([#269](https://github.com/kindspec/rowspec/issues/269)).

By default, computed columns are live formulas over structured references,
such as `rowspec[[#This Row],[qty]]`, and the aggregates are `SUBTOTAL` forms.
No formula holds a coordinate. The formulas are written to
carry this format's rules rather than the spreadsheet's: a blank operand, text
in a summed column, or the minimum of nothing is an error, not a `0`. A `#REF!`
arrives as a spreadsheet error value, though without the name in its
parentheses.

A formula workbook computes with spreadsheet arithmetic, which is not this format's.
Tolerant comparison and subtraction can make an `if` take the other branch
([#88](https://github.com/kindspec/rowspec/issues/88)), and left-to-right
addition can cancel a total that §7's exact sum keeps
([#83](https://github.com/kindspec/rowspec/issues/83)). The key column is text,
so a formula using it as a number is an error in the workbook. Hidden or
filtered rows drop out of the `SUBTOTAL` aggregates but not out of `count`.

What a spreadsheet formula cannot say, the default export refuses rather than
approximates, and writes nothing: `cumulative`, `prior` and `delta`; any `where` predicate;
and a few narrower cases listed in `export/rowspec_xlsx/__init__.py`.

**What is checked is agreement on the conformance tree, not in general.**
`just test-libreoffice` exports every `.mdtbl` in the conformance tree that
rowspec accepts and the exporter can express. It recalculates each one in
headless LibreOffice and compares every computed cell and aggregate with
`rowspec eval`. Numbers are compared at 15 significant digits, which is all
LibreOffice saves. CI runs it. Where they disagree, the test pins the value
LibreOffice gives, so a change in either direction fails it. That covers four
`sum` and `avg` cases from the tree near `1e308`, plus two tables written for
the test: `if(c = 0.3, …)` over `0.1 + 0.2` (#88), and `1e16 + 1 - 1e16` (#83).
Both kinds of disagreement occur at ordinary magnitudes, so a table outside
the tree can disagree in ways nothing here checks.

**Which mode is exact.** `--values` is exact, and the default is not. The
default writes formulas, and a spreadsheet recalculates them with its own
arithmetic, which can disagree with `rowspec eval` as described above
([#83](https://github.com/kindspec/rowspec/issues/83),
[#88](https://github.com/kindspec/rowspec/issues/88)). `--values` writes
`rowspec eval`'s computed values in place of the formulas, at full binary64
precision, so its computed cells and aggregates are exactly the format's, as
are its stored numbers
([#89](https://github.com/kindspec/rowspec/issues/89)). Each `#REF!` is written
as the spreadsheet error `#REF!`, an error cell and not text, so a spreadsheet
`SUM` over it is an error rather than skipping it. The name in its parentheses
is lost, as in the default mode. The cost is that nothing in the workbook
recalculates: it is the table as it was computed at export, and editing a cell
in the spreadsheet changes no total.

With no formula to write, `--values` exports `cumulative`, `prior`, `delta`,
`where` predicates, and the other tables the default refuses only because no
formula says them. It still refuses what a spreadsheet table cannot hold:
column names that differ only by case, a table with no rows, and a character
XML has no place for.

`just test-xlsx` exports every `.mdtbl` in the conformance tree that rowspec
accepts with `--values`, reads each saved file back, and compares every
computed cell and aggregate with `rowspec eval`: the same binary64 number, an
error cell for each `#REF!`, and no formula anywhere. The LibreOffice test
does not apply to this mode. It checks what a spreadsheet engine recalculates,
and a values workbook gives it nothing to recalculate. Its comparison also
stops at 15 significant digits, which is all LibreOffice saves, so it could not
check the last digits this mode exists to keep.
