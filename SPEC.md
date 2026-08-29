<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# rowspec — specification, draft 0

Status: draft. **Where this document and the conformance suite disagree, the
suite wins and this document is in error.** That ordering is deliberate: it is
the lesson of CommonMark's founding grievance, that early implementers had to
consult a buggy reference program because no executable spec existed.

Conformance is a claim about a **version of the suite**, not about this prose.
An implementation states: *conforms to rowspec suite 0.x*.

---

## 1. What this format is for

A table that several people edit, in git, over years, where a merge that is
quietly wrong is worse than a merge that fails.

Everything below follows from one rule:

> **Serialize so that the unit of merge is the unit of meaning.**

Git merges by line. So one line is one row, names are never coordinates, and
anything that cannot be made safe is refused rather than guessed at.

## 2. Deliberately left open

An implementation may do as it likes with: rendering and alignment on screen,
number formatting and locale display, the function library beyond §7, indexing
and caching, editor behaviour, and how a conflict is shown to a human.

**Deliberately specified**, because two implementations that disagree here
produce silent corruption rather than an argument: the exact set of refusals
(§9), row ordering (§6), reference resolution and error propagation (§7–8), and
the canonical byte form (§10).

An undocumented degree of freedom becomes an interoperability bug the moment two
implementations meet in one repository.

## 3. Encoding

UTF-8, no BOM. Identifiers are compared after Unicode **NFC** normalisation;
`Cf` format characters are rejected in identifiers, so that two visually
identical names cannot coexist.

**Line endings are preserved.** LF and CRLF are both accepted and round-trip
byte-exactly; only the *canonical* form (§10) is LF. A lone `CR` is **refused**:
it makes two rows share one git line, which breaks the format's founding rule
that one line is one row.

Enforced by the parser, not by `.gitattributes`, because a bare repository never
reads `.gitattributes` and a fresh clone never has local configuration. NFD
renormalisation is measured to turn a one-word edit into a four-line diff and to
make two edits to different rows conflict with both sides pixel-identical.

## 4. File shape

    <table>
    <blank line>
    <declarations>

The table is a contiguous run of lines beginning with `|`. The first is the
HEADER, the second is the ALIGNMENT row, the rest are DATA rows. File extension
`.mdtbl`.

**The alignment row is required, and its syntax is exactly this:** each cell is
one of `---`, `:--`, `--:`, `:-:`, where the run of hyphens is one or more. Any
of these spellings is accepted; §10 fixes which one is canonical. Its field
count must equal the header's.

**If the second table line is not a valid alignment row, the file is refused.**
It is never reinterpreted as a data row. This rule exists because the
alternative is a silent data loss: an implementation that treats an
unrecognised alignment row as data, or a missing one as present, consumes a row
of the user's data and reports a plausible total. A reader that cannot recognise
a construct MUST refuse it, and MUST NOT degrade a failed recognition into a
different successful one.

**Cell values are trimmed of leading and trailing ASCII space and horizontal
tab, and of nothing else.** A non-ASCII space is not padding: §8 lists it among
the values that must not be interpreted, and in practice it arrives only by
paste from a locale-aware spreadsheet, where it is a thousands separator.
Trimming it would silently turn `1 500` into `1500`.

Whitespace is also **rejected in identifiers** — column names, aggregate names
and row keys — for the same reason §3 rejects `Cf`: two identifiers that render
identically must not be able to coexist, or the duplicate-key refusal never
fires.

## 5. Columns

A header cell is a NAME, or a name and a formula separated by `=`:

    | id | item | qty | unit | total = qty * unit |

Column names are a namespace, and it is the only namespace in the format that
is **co-located** — all of it on one line — so a collision between two authors
is a line collision that stock git refuses on its own. Every other namespace
relies on §9.

A column with a formula is COMPUTED and its data cells are empty. Writing a
value into a computed cell is an error.

## 6. Rows, identity, and order

    key   := id
    order := by(date)      # or omitted entirely

**The key** column holds an opaque, machine-generated row identifier. It is not
an address: a human writes column *names* into formulas and never writes a row
id into anything.

Measured rationale: across four identity functions and four concurrent-edit
scenarios, natural keys lose an edit on rename and overwrite a row on
duplication; content hashes split one row into two; only an opaque id survives
all four. Every failure was silent.

**Order.** Without `order`, the table is a SET and the row-relative operators of
§7 are refused. With `order := by(c)`:

- `key` is **required**. Without it, tied order values fall back to physical
  file position, which is a coordinate.
- `c` must be a stored column, never a computed one.
- `c` must have a single type across all rows — `number`, `date`
  (`Y-M-D` or `Y/M/D`), or `text`. **Mixed types are refused**, because they
  have no total order.
- The sort key is the **tuple** `(typed value of c, key)`. It is never a string
  concatenation: concatenating lets the row id decide the order of rows whose
  keys differ, which would make the id an address after all.
- Non-finite numbers in `c` are refused.

**A row's position in the file is never an input to any computation.** Shuffling
every line leaves all values unchanged. A backdated row appended last still
leads a running total.

## 7. Formulas

Arithmetic over column names, referring to the current row.

**Row-relative** operators, legal only under a declared order, evaluated over
the derived order and never over file position:

    cumulative(c)   running total
    prior(c)        that column's value in the preceding row
    delta(c)        c minus prior(c)

**Per-row group aggregates.** `@c` means *this row's* value of `c`:

    | region_total = sum(amount where region = @region) |
    | rep_share    = sum(amount where region = @region and rep = @rep) |

The predicate is a conjunction of equalities against a literal or an `@`
reference. This is the nominal form of `SUMIF`/`SUMIFS`.

**Cross-artifact lookup**, resolved by the target's own declared key:

    | who = lookup(customers.mdtbl, customer, name) |

The target is a **literal** path written in the formula, resolved relative to
the referring artifact, and confined to the repository. It is never computed at
evaluation time. This is the only form of path reference the format has, and it
is what §8's prohibition on reading paths excludes: a reader can see every file
an artifact depends on by reading the artifact.

**Table-level aggregates**, declared below the table, one per line:

    grand := sum(total)
    eu    := sum(total where region = "EU")

Functions: `sum`, `count`, `min`, `max`, `avg`. An unknown function is refused.

## 8. Errors propagate; they never degrade

A reference to a name that does not exist evaluates to `#REF!(name)`. An
aggregate over any column containing a `#REF!` is itself `#REF!` — **it must not
sum the values it can read**. A lookup whose target row is absent is
`#REF!(file[key])`.

A broken reference never evaluates to zero, empty, or a stale value. A blank
cell is not zero. A value that will not coerce to a number is `#REF!`, not a
guess: thousands separators, parenthesised negatives, and non-ASCII spaces are
refused rather than interpreted.

The evaluator is total, terminating, deterministic and free of input/output.
There is no flag that changes this. Constructs that would read the clock, the
network, or a path are not blocked — they are unparseable. This is
simultaneously a security property and a correctness one: a content-addressed
cache is silently wrong if a formula can read the clock.

## 9. Refusals — normative

Recognition is total: every byte sequence has exactly one defined outcome, and a
parse error is *reported* separately from being *handled*, so a validator and an
evaluator run the same algorithm and differ only in what they print.

An implementation MUST refuse:

1. conflict markers anywhere in the file
2. a duplicate column name
3. a duplicate aggregate name
4. a duplicate `key` or `order` declaration
5. a duplicate row id, where a key is declared
6. a data row whose field count differs from the header
7. an alignment row whose field count differs from the header
8. an alignment-style row among the data rows
9. a row-relative operator with no declared order
10. `order := by(c)` where `c` is not a stored column, is computed, or mixes types
11. an unknown aggregate function
12. a malformed declaration
13. a file containing no table

**Reject when degrading could yield a plausible VALUE; preserve and warn when it
could only lose DECORATION.**

Exactly one ignorable channel exists: **a line whose first non-space character
is `#`, outside the table**. It is preserved verbatim by `render` and by `canon`,
and it carries an *inertness promise*: nothing in it may ever contribute to a
computed value. That promise is testable — strip every annotation and assert no value
changes.

Refusing is not the same as being strict for its own sake. A policy that refuses
everything unknown was measured to reject 6 of 12 files that had a correct
answer, one differing from a valid file only by a comment.

## 10. Canonical form

    | id | item | qty | unit | total = qty * unit |
    | --- | --- | --: | --: | --: |
    | r_0001 | widget | 10 | 12.00 |  |

Single-space delimiters, **no alignment padding**. Padded input is valid and
round-trips byte-exactly; it is simply not canonical, and canonicalisation is a
separate explicit operation with `canon(canon(x)) == canon(x)`.

Measured on 2,000 rows, changing one cell from `9` to `1000`:

    padded      2002 added / 2002 removed lines, 238,370 bytes of diff
    canonical      1 added /    1 removed line,      413 bytes

and, decisively, two **genuinely disjoint** edits conflict when padded and merge
cleanly when canonical. A widening cell reflows every row, so alignment
manufactures conflicts between edits that never touched each other.

## 11. Version control

An implementation MUST NOT require a git merge driver, a clean/smudge filter, or
a hook for correctness. `.gitattributes` travels but `merge.<name>.driver` does
not; a fresh clone silently falls back to line merge; and a **bare repository
does not consult `.gitattributes` at all**, which is what every forge merges in.
GitLab documents that custom merge drivers are unsupported on GitLab.com.

Correctness therefore lives in the representation. Type-aware merge may improve
the experience and must never be required for the result.

Where a tool merges on behalf of a user, it must **merge and then validate every
changed path**. `git merge-tree` reports only the paths where git *failed*;
where git merges cleanly and wrongly there are no conflict stages at all, so a
tool that only inspects conflicts will publish git's wrong answer.

## 12. Versioning

One repository-level file, `.rowspec`, containing `edition <year>`.

A reader **never consults it** — interpretation is a function of the artifact's
bytes alone, so there is no "unknown version" case to mishandle. A writer emits
only what its edition permits. Artifacts of different editions coexist in one
repository with no ceremony, and migration rewrites to the *intersection* —
valid under both editions — so it is incremental rather than atomic.

A per-file version field is rejected: it would touch every file on a bump, and a
version line at line 1 conflicts with any concurrent edit to the header row.

## 13. Conformance

`conformance/cases/` holds the suite as directories of real files plus one
`expect.json` each. A conforming implementation runs them against a **stock git
binary**. Merge cases assert on the **evaluated value** of the merged artifact,
not on git's exit code, because a clean merge with a wrong number is the failure
that matters.

An implementation SHOULD also run the mutation gate. A suite that cannot fail a
deliberately broken implementation is measuring nothing.
