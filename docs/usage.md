<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Using rowspec

## It runs on the CSV you already have

```sh
rowspec check data/
```

No migration. On an ordinary `.csv` that alone refuses a committed conflict
marker — which Python's own `csv` module parses as valid rows without
complaint — a duplicate column name, a ragged row, invalid UTF-8, and an
invisible character in a column name. A five-line
`data/countries.csv.rowspec.json` naming the key and the order column adds the
rest. See [csv.md](csv.md), and copy
[ci/rowspec-check.yml](ci/rowspec-check.yml) into
`.github/workflows/`.

### In CI, in three lines

```yaml
- uses: actions/checkout@v7
- uses: kindspec/rowspec@v0.6.1
  with:
    paths: data
```

It runs **both** commands, because that is the whole reason it exists: `check`
applies the structural refusals, `eval` computes every table and fails on an
unresolved value, and **neither subsumes the other**. A misspelled column name
or a pasted `1,299.00` is `#REF!` and correctly *not* a structural refusal, so
a pipeline with only `check` is green on a broken total.

The action's own test suite proves that in both directions: one job asserts it
passes a good tree, and another feeds it a well-formed table whose total is
`#REF!` and asserts the action **fails** — then runs the same file with
`eval: false` and asserts it **passes**, so the first assertion is about `eval`
and not about the file.

Or copy [ci/rowspec-check.yml](ci/rowspec-check.yml) if you would
rather own the workflow.

Run against 1,564 CSVs in three public data repositories it refused 16: two
grouped-header spreadsheet exports, thirteen truncated CDC snapshots in
`owid/covid-19-data` whose header declares 14 columns for a 6-field row, and
one deliberately broken fixture in `iptv-org/database`'s own test suite. No
false positives.

## Edit a table

```sh
rowspec add-row parts.mdtbl bolt 4 0.10                # one added line, where its key sorts
rowspec add-row parts.mdtbl bolt 4 0.10 --after r_01   # or beside a key, if that keeps key order
rowspec add-row parts.mdtbl bolt 4 0.10 --id r_09      # a chosen id
rowspec rename-column parts.mdtbl qty quantity         # header, formulas, declarations
rowspec add-column parts.mdtbl note --after item       # every row gains a cell
rowspec delete-column parts.mdtbl note                 # refused while anything names it
```

Rows stay in key order (`SPEC.md` §6), and a table whose rows are out of order
is refused as `rows-out-of-order`. `rowspec check --fmt --sort-rows` is the
migration: it rewrites such a file with the rows sorted by key, each line whole,
and a file with any other refusal stays refused and unchanged. Plain `--fmt`
never sorts, so a format step can't do this unasked. After a merge, a row out of
order may be one another branch deleted, and sorting would keep it: check that
first. Sort a table when no branch that deletes its rows is open, since the sort
is itself a move (§6).

Each edit changes only the lines it is about, so that edits on two branches
merge wherever they do not touch neighbouring lines, and a refused edit leaves
the file as it was. A program can call `rowspec.edit` directly;
[editing-api.md](editing-api.md) has the operations, the diff each
one makes, and what it refuses.

## Two commands, and you need both

`check` applies the refusals in §9 — the structural ones, the things that make a
table survive version control. `eval` computes the table and fails on any
`#REF!`.

**They catch different things and neither subsumes the other.** A misspelled
column name, a pasted `1,299.00`, or a non-breaking space in a number are all
`#REF!` under §8 and are correctly *not* §9 refusals — the file is well-formed,
its total is wrong. `check` alone reports `0 refused` on a table whose total is
wrong, so a CI recipe built on `check` is green on a broken total.

Run both:

```sh
rowspec check .    # will this table survive being edited by several people?
rowspec eval  .    # does it currently say anything false?
```

A refusal names its §9 identifier, so a program can tell the refusals apart
without parsing the message. Plain output ends the line with it, and
`--format github` puts it in the annotation's title:

```
data/parts.mdtbl: duplicate key id='r_1' [duplicate-row-id]
::error file=data/parts.mdtbl,title=rowspec [duplicate-row-id]::duplicate key id='r_1'
```

A refused `.csv` or `.tsv` prints the §9 identifier SPEC.md §13 reads its
refusal as, in the same two places. Warnings carry no identifier, and
neither does a warning `--strict` turns into a refusal.

## From the source archive

**From the source archive (sdist), install the `conformance` extra.** The
sdist ships the fixture tree and the runner, and the runner needs
[kindkit](https://github.com/kindspec/kindkit). The extra declares it, so pip
is enough (#47). Unpack the archive, then, at its top level:

```sh
python -m venv .venv && . .venv/bin/activate
pip install '.[conformance]'
cd conformance && python run_cases.py     # cases/; add --profile csv for cases-csv/
```

Without the extra, the runner stops at its kindkit import with
`ModuleNotFoundError: No module named 'kindkit'`. `uv sync` (or `just setup`)
then `just conform` works too: the `dev` group pins the exact kindkit release
CI runs, and the extra admits that release.

## Every recipe

```sh
just setup      # uv sync
just check      # fmt-check + lint
just test       # everything under tests/: suite, gate, CSV, CLI, boundary
just conform    # the suite alone, against a stock git binary
just mutants    # deliberately break the implementation; the suite must notice
just conform-alt # the SECOND implementation, against the same fixture tree
just test-xlsx  # the exporter, WITH its optional extra installed
just test-libreoffice # exported workbooks recalculated by LibreOffice
just run FILE   # validate an artifact (rowspec check)
just eval FILE  # print computed values and FAIL on any #REF!
```

A real `git` binary is required. The suite's central claim is about what stock
git does, so it uses stock git.
