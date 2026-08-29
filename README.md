# rowspec

A specification and executable conformance suite for tabular data that must
survive version control.

A `.mdtbl` file is a markdown table where a computed column carries its formula
in the header, rows have opaque ids, and nothing is addressed by position. The
point is that **stock git merges it correctly, or refuses — never quietly
wrong**, with none of this project's tooling installed.

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
number that is 27% wrong, with no marker anywhere. That difference is the
entire project.

## It runs on the CSV you already have

```sh
rowspec check data/
```

No migration. On an ordinary `.csv` that alone refuses a committed conflict
marker — which Python's own `csv` module parses as valid rows without
complaint — a duplicate column name, a ragged row, invalid UTF-8, and an
invisible character in a column name. A five-line
`data/countries.csv.rowspec.json` naming the key and the order column adds the
rest. See [docs/csv.md](docs/csv.md), and copy
[docs/ci/rowspec-check.yml](docs/ci/rowspec-check.yml) into
`.github/workflows/`.

Run against 1,564 CSVs in three public data repositories it refused 16: two
grouped-header spreadsheet exports, thirteen truncated CDC snapshots in
`owid/covid-19-data` whose header declares 14 columns for a 6-field row, and
one deliberately broken fixture in `iptv-org/database`'s own test suite. No
false positives.

## What is actually shipped

The **conformance suite** is the deliverable. It checks out two branches, runs
stock `git merge`, evaluates the merged file, and asserts on the computed
number. No prior art does this. The spec, the validator and the reference
implementation exist so the suite has something to check.

## Run it

```sh
just setup      # uv sync
just check      # fmt-check + lint
just test       # conformance suite + mutation gate + corpus checks
just conform    # the suite alone, against a stock git binary
just mutants    # deliberately break the implementation; the suite must notice
just run FILE   # validate an artifact
```

A real `git` binary is required. The suite's central claim is about what stock
git does, so it uses stock git.

## Licensing

Per directory, deliberately — see [LICENSE](LICENSE). The fixtures are CC0 so
they can be vendored into an implementation in any language under any licence.

## Credit

Standing on Coopy/daff, ClassSheets, Object Spreadsheets, Lotus Improv and
org-mode. See [NOTICE](NOTICE).
