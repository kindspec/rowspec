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
number that is 27% wrong, with no marker anywhere. That difference is the entire
project.

## What it does not do, measured

**If your table is a list of facts, you probably do not need this.** We replayed
7,446 real commits from four public CSV-in-git registries, including 528 real
three-way merges. Neither `.mdtbl` nor plain CSV ever merged silently wrong.
For an ordinary sorted registry CSV, **stock git already does what this format
promises**, and none of those maintainers has wanted a computed column in four
years.

The format earns its keep when a table **computes** — when a merge can leave a
total that is quietly wrong, which is the failure a CSV cannot even represent.

**Two branches each adding a column conflict badly**, across most of the file.
That is inherent to one-row-per-line and it is exactly what happens to a CSV.
Nothing here fixes it; a column addition rewrites every row either way.

**It is not a data-quality tool.** Whether a country code is in ISO 3166,
whether a URL resolves, whether a date is plausible — none of that is here, and
[Frictionless](https://frictionlessdata.io/) does it well. rowspec asks a
smaller question: will this table survive being edited by several people over
years?

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

### In CI, in three lines

```yaml
- uses: actions/checkout@v7
- uses: kindspec/rowspec@v0.1.0
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

Or copy [docs/ci/rowspec-check.yml](docs/ci/rowspec-check.yml) if you would
rather own the workflow.

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

    410 conformance cases          two implementations, both passing
     76 mutants                    74 killed, 0 survived, 0 stale

**The second implementation is the point.** `reference/rowspec_alt/` was written
from `SPEC.md` alone by an author forbidden to read `reference/rowspec/`, and it
runs against the same fixture tree in CI on every push. It is the only evidence
that this document *defines* the format rather than describing one program, and
it has repeatedly been the half that was right: on the last three questions
where the two disagreed, the independent implementation was correct and the
reference was wrong.

**The mutation gate is the other half.** The suite is only worth its green tick
if it can go red, so the implementation is deliberately broken in 76 specific
ways and the suite must notice every one. A mutant that survives is reported as
a failure, and so is a *stale* one whose pattern no longer matches the source —
because a check that quietly stopped running is the failure this project keeps
finding in itself.

Neither number is a claim about correctness in general. See
[docs/rationale.md](docs/rationale.md) for what has been measured, and what has
been measured and found wanting.

## Run it

```sh
just setup      # uv sync
just check      # fmt-check + lint
just test       # conformance suite + mutation gate + corpus checks
just conform    # the suite alone, against a stock git binary
just mutants    # deliberately break the implementation; the suite must notice
just conform-alt # the SECOND implementation, against the same fixture tree
just run FILE   # validate an artifact (rowspec check)
just eval FILE  # print computed values and FAIL on any #REF!
```

A real `git` binary is required. The suite's central claim is about what stock
git does, so it uses stock git.

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

## Licensing

Per directory, deliberately — see [LICENSE](LICENSE). The fixtures are CC0 so
they can be vendored into an implementation in any language under any licence.

## Credit

Standing on Coopy/daff, ClassSheets, Object Spreadsheets, Lotus Improv and
org-mode. See [NOTICE](NOTICE).
