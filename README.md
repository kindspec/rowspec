# rowspec

A file format and test suite for tables that must survive version control.

A `.mdtbl` file is a markdown table where a computed column carries its formula
in the header, rows have opaque ids, and nothing is addressed by position. So
**a merge can't leave a formula pointing at the wrong row**, with none of this
project's tooling installed. `rowspec check` and `rowspec eval` catch a merge
that duplicates an id or leaves a name undefined. Not every bad merge is flagged: a row
moved on one branch and deleted on the other comes back, as the
[editing API notes](https://github.com/kindspec/rowspec/blob/main/docs/editing-api.md)
explain.

```
| id     | item   | qty | unit  | total = qty * unit |
| ------ | ------ | --: | ----: | -----------------: |
| r_0001 | widget |  10 | 12.00 |                    |

key   := id
grand := sum(total)
```

Two branches insert a row far apart. Stock `git merge` — no driver, no
`.gitattributes`, nothing installed — merges cleanly, and `grand` is correct.
The same table with `A1`-style references merges just as cleanly and reports a
number that is 27% wrong, with no marker anywhere. That difference is the entire
project.

## Quick start

```sh
pip install rowspec
rowspec check .    # will this table survive being edited by several people?
rowspec eval  .    # does it currently say anything false?
```

Run both. `check` finds structural problems, and `eval` computes every table
and fails on an unresolved value. A misspelled column name passes `check` and
leaves a wrong total, so `check` alone is not enough.

Already have CSV files? `rowspec check data/` works on them with no migration.
See [CSV mode](https://github.com/kindspec/rowspec/blob/main/docs/csv.md).

## In CI

```yaml
- uses: actions/checkout@v7
- uses: kindspec/rowspec@v0.6.1
  with:
    paths: data
```

The action runs both commands.

## Edit a table

```sh
rowspec add-row parts.mdtbl bolt 4 0.10
rowspec rename-column parts.mdtbl qty quantity
rowspec add-column parts.mdtbl note --after item
```

Each edit changes only the lines it is about, so edits on two branches merge
wherever they don't touch neighbouring lines. Programs can call `rowspec.edit`;
see the [editing API](https://github.com/kindspec/rowspec/blob/main/docs/editing-api.md).

## Do you need it?

**If your table is a list of facts, you probably do not need this.** Across 7,446 real commits
from four public CSV-in-git registries, including 528 real three-way merges,
neither `.mdtbl` nor plain CSV ever merged silently wrong.

It earns its keep when a table **computes**, and a merge can leave a total that
is quietly wrong. It doesn't help when two branches each add a column, which
conflicts as badly as it does in CSV. It isn't a data-quality tool either; for
that, use [Frictionless](https://frictionlessdata.io/).

## How it is tested

The test suite is the main deliverable. It checks out two branches, runs stock
`git merge`, evaluates the merged file and asserts on the computed number. A
second implementation, written from `SPEC.md` alone, runs against the same
cases, and a mutation gate breaks the code on purpose to prove the suite
notices.

    643 conformance cases          two implementations, both passing
    118 mutants, all distinct      116 killed, 2 equivalent
                                     0 survived, 0 stale, 0 broken

## Documentation

| | |
|---|---|
| [SPEC.md](https://github.com/kindspec/rowspec/blob/main/SPEC.md) | the format |
| [Using rowspec](https://github.com/kindspec/rowspec/blob/main/docs/usage.md) | CSV files, CI, editing and the two commands in full |
| [Export to xlsx](https://github.com/kindspec/rowspec/blob/main/docs/xlsx.md) | `pip install 'rowspec[xlsx]'`, formulas or values |
| [What has been measured](https://github.com/kindspec/rowspec/blob/main/docs/evidence.md) | what it does not do, and how the suite is built |
| [Rationale](https://github.com/kindspec/rowspec/blob/main/docs/rationale.md) | why the format is this way |

## Develop

A real `git` binary is required, because the suite's central claim is about
what stock git does.

```sh
just setup      # uv sync
just check      # fmt-check + lint
just test       # everything under tests/
just conform    # the suite alone, against a stock git binary
just mutants    # break the implementation; the suite must notice
```

See [CONTRIBUTING](https://github.com/kindspec/rowspec/blob/main/CONTRIBUTING.md) and `just --list`.

## Licensing

Per directory, deliberately. See [LICENSE](https://github.com/kindspec/rowspec/blob/main/LICENSE). The fixtures are CC0 so
they can be vendored into an implementation in any language under any licence.

## Credit

Standing on Coopy/daff, ClassSheets, Object Spreadsheets, Lotus Improv and
org-mode. See [NOTICE](https://github.com/kindspec/rowspec/blob/main/NOTICE).
