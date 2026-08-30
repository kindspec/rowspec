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

UTF-8, no BOM. Identifiers are compared after Unicode **NFC** normalisation.

`Cf` format characters cannot appear in identifiers, but this is a
**consequence** of §4.1.9's allowlist rather than an independent rule — the
allowlist admits letters, marks, digits and underscore, and `Cf` is none of
them. It is stated here because the *reason* matters and the allowlist does not
carry it: two identifiers that render identically must not be able to coexist,
or the duplicate-key refusal never fires.

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

### 4.1 Lexical grammar — normative

The layer the rest of this document assumed. Where a rule is a **decision**
rather than a description of settled behaviour it is tagged **[CHOICE]**.

ABNF, with `WSP = SP / HTAB` — ASCII space U+0020 and horizontal tab U+0009,
never the Unicode `White_Space` property — and `DIGIT = %x30-39`, ASCII only.
`LETTER`, `MARK` and `NUM` are the Unicode general categories `L*`, `M*`, `N*`.
`char` is any scalar value other than `CR` or `LF`.

```abnf
file        = *line
line        = conflict / annotation / table-line / blank / declaration
eol         = LF / CRLF                       ; a lone CR is refused (§3)
blank       = *WSP eol
conflict    = ( 7"<" / 7"=" / 7">" / 7"|" ) *char eol
annotation  = *WSP "#" *char eol
table-line  = *WSP "|" 1*( cell "|" ) *WSP eol
cell        = *( char - "|" )                 ; no escape exists
declaration = *WSP ident *WSP ":=" *WSP rhs [ 1*WSP "#" *char ] eol
rhs         = ident "(" *WSP arg *WSP ")" / ident
arg         = ident [ 1*WSP "where" 1*WSP predicate ]        ; predicate: §7
ident       = 1*( LETTER / MARK / NUM / "_" / "-" / "." )
align-cell  = [ ":" ] 1*"-" [ ":" ]
number      = [ "-" ] 1*DIGIT [ "." 1*DIGIT ]
date        = 1*4DIGIT "-" 1*2DIGIT "-" 1*2DIGIT
            / 1*4DIGIT "/" 1*2DIGIT "/" 1*2DIGIT
```

**Classification order is normative.** The alternatives of `line` are tried in
the order written and the first that matches decides what the line is. Two of
those orderings carry real weight. `conflict` precedes `table-line` because
`|||||||` is *itself* a well-formed seven-cell table line, so a reader that
recognises tables first parses a diff3 conflict as rows of data and totals them.
`annotation` precedes `table-line` because `# | r_9999 | ghost | 100 |` must
stay inert; a reader that recognises tables first gains a row from a comment.
A line matching no alternative is refused (§9.19) and is never skipped: a
skipped line is a missing row, and a missing row is a plausible smaller total.

**1. Lines.** `LF` and `CRLF` are both `eol` and both round-trip byte-exactly
(§3). The terminator on the file's last line is optional; its presence or
absence is part of the file's bytes, is preserved by `render`, and never changes
the parse. `canon` terminates every table line it emits and leaves annotations
and declarations byte-verbatim.

**2. The table.** The table is the *maximal contiguous run* of `table-line`s.
Annotations and blank lines may precede and follow it; they may not appear
inside it. A `#` line between two data rows therefore ends the run, and the next
table line is a table line after the table, which is refused (§9.19). A file has
exactly one table. **[CHOICE]** — §9 defines the ignorable channel as "outside
the table" and §4 calls the run contiguous, but the two readings left open
(skip the `#` line and continue the table; or start a second table) each change
how many rows the file has without saying so, which is the divergence §1 exists
to prevent.

**3. The pipe.** Both the leading and the closing `|` are required. **A cell can
never contain `|`, because no escape exists and none may be invented.** An
implementation that adds one — `\|`, `||`, a quoted cell — makes a file whose
field count differs between readers, so one reader sees the row the author wrote
and the other sees a row with an extra field or a truncated value. **[CHOICE]**
The closing `|` is required rather than optional as in GFM: it is the only thing
that distinguishes a row truncated inside its final cell from a shorter one, and
the field-count refusal (§9.6) cannot see that truncation because the field count
does not change. `WSP` before the leading `|` and after the closing `|` is
decoration: `canon` drops it and `render` restores it byte-exactly.

**4. Cell values.** A cell's value is its text with leading and trailing `WSP`
removed, and nothing else removed — the rule and its reason are in §4 above and
in §8: U+00A0, U+202F and U+2007 in padding position arrive by paste from a
locale-aware spreadsheet, where they are thousands separators, so trimming them
turns `1 500` into `1500`. Trimming is also what makes text comparison total: a
row keyed `r_01` and a row keyed `<tab>r_01` must be one duplicate (§9.5), not
two rows that render identically.

**5. The alignment row.** Every cell of the second table line, trimmed, must
match `align-cell`; `:--`, `--:`, `:-:` and `---` are the four spellings, the
hyphen run is one or more, and `| - |` is the minimal form. An empty cell is not
an `align-cell`, and neither are `::`, `-- -`, or an en dash: none is one of the
four spellings, and §4's rule then applies — the file is refused rather than
reinterpreted. A *data* row is alignment-style (§9.8) if and only if **every**
one of its cells matches `align-cell`; a single cell of `---` beside ordinary
values is data.

**6. Numbers.** A cell is read as a number only if it matches `number`. Refused,
and therefore text — `#REF!` when used as an arithmetic or aggregate operand
(§8): a leading `+`, exponent notation (`1e3`), a bare `.5` or `5.`, digit
grouping of any kind (`1,000`, `1_000`, `1 000`), a parenthesised negative
(`(500)`), a radix prefix (`0x10`), and `inf`, `nan` and `infinity` in any case.
`DIGIT` is U+0030–U+0039 and nothing else: `\d` in Python, Java and .NET also
matches Arabic-Indic `٥` and thirty other digit families, so a naive
implementation reads `٥` as five while a strict one reads it as text — the same
cell, two totals, no error. **[CHOICE]** Exponents, a leading `+`, and the
one-sided decimal point are refused rather than accepted: each is a second
spelling of a value that already has one, and a second spelling compares equal
as a number and unequal as text, which splits `where` predicates and key
identity from arithmetic.

That reason is broader than the list it justifies, and deliberately so: `007`
and `1.50` satisfy it exactly and are **admitted**, because refusing them would
break zero-padded identifiers and currency columns — both of which are ordinary
and neither of which is a typo. The rule is the list, not the reason. Anyone
extending the grammar should weigh the cost to real data before applying the
reason to a new spelling.

**7. Dates.** A cell is a date only if it matches `date`; the two separators
within one date must be the same character. **[CHOICE]** — `2024-01/05` is a
typo, and a format that accepts it accepts a value nobody wrote. Mixed spellings
in *different rows* of one column are all dates and do not make the column mixed
(§6). There is no calendar validation: `2024-13-45` matches `date` and orders as
written, because a lexical layer that rejected it would have to know about leap
years to be consistent. **Dates compare as the integer tuple `(y, m, d)`, never
as strings.** String comparison sorts a hand-typed `2026-2-1` after `2026-03-01`
because `'2' > '0'`; §6's order then drives `cumulative`, so an overdraft check
reads a running balance of `55.0` where the truth is `5.0` — a plausible number,
not an error.

**8. Text order.** A `text` order column (§6), and the row-key tiebreak of §6's
sort tuple, compare by **Unicode code point** over the NFC-normalised, trimmed
value. Locale collation is refused, not merely not required: it makes the
interpretation of an artifact a function of the reading machine's locale and ICU
version rather than of the artifact's bytes, so the same commit yields two row
orders — and under `cumulative` two sets of numbers — on two developers'
machines, with no diagnostic on either. §12 makes the same commitment for
editions: interpretation is a function of the bytes alone.

**9. Identifiers.** Column names, aggregate names, the argument of `key` and
`order`, and the values of the key column are `ident`: one or more Unicode
letters, marks or digits, `_`, `-`, `.`. Whitespace and `Cf` are excluded by
construction, which is what §3 and §4 require; so are `|`, `=`, `:`, `#`, `(`,
`)`, `,`, `"` and `@`, each of which is structural somewhere — a column named
`total (USD)` would be unquotable inside a formula, and `#` would be
indistinguishable from an annotation. **[CHOICE]** The set is an allowlist
rather than a denylist so that the answer for a character nobody has thought of
yet is *refused*, not *whatever this implementation's punctuation table happens
to say*.

**10. Annotations.** Two forms, and only two. A whole-line annotation is a line
whose first non-`WSP` character is `#`, outside the table; everything after the
`#` is inert, whatever it looks like — `# key := id` is an annotation, not a
malformed declaration, because commenting a declaration out is the reason the
channel exists. An inline annotation is `WSP` followed by `#` to end of line, on
a **declaration line only**; `g := sum(v)# note` has no whitespace before the
`#` and is a malformed declaration. **`#` inside a table line is data**, never
an annotation: cells legitimately hold `#4`, `#widget` and `#ff8800`, there is
no escape (rule 3), and an inline channel inside the table would make those
values unwritable while silently truncating the rows that contain them.

**11. Declarations.** `name := fn(arg)`, with optional `WSP` anywhere `*WSP`
appears in the grammar; `key := col` is the sole bare form, because `key` names
a column rather than computing one. A declaration is malformed (§9.12) if it
contains `:=` and does not match `declaration` — including a non-`key` name with
no function, an unclosed parenthesis, an unrecognised `order` construct such as
`order := none()`, and any `ident` violating rule 9. §6 defines exactly two
order states, `order := by(c)` and the line omitted entirely; a third spelling is
refused rather than degraded into the second.

**12. Conflict markers.** A conflict line is any line whose first seven
characters are seven `<`, seven `=`, seven `>`, or **seven `|`**. All four,
including the diff3 base marker `|||||||`, are refused wherever they appear
(§9.1) — before any other classification, per the ordering rule above.

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

**`lookup` is reserved and not defined in this edition.** A cross-artifact
reference is a real requirement — roughly a fifth of real spreadsheet lookups
already target another file — but it was the sole source of input/output inside
an otherwise pure evaluator, of path confinement against a repository root
nothing defines, of cross-artifact cycles, and of the consequence that an
artifact's validity depends on more than its own bytes. It is reserved so a
later edition can define it without a migration. Cases for it are kept, unrun,
in `conformance/reserved/`.

**Table-level aggregates**, declared below the table, one per line:

    grand := sum(total)
    eu    := sum(total where region = "EU")

Functions: `sum`, `count`, `min`, `max`, `avg`. An unknown function is refused.

## 8. Errors propagate; they never degrade

A reference to a name that does not exist evaluates to `#REF!(name)`. An
aggregate over any column containing a `#REF!` is itself `#REF!` — **it must not
sum the values it can read**.

A broken reference never evaluates to zero, empty, or a stale value. A blank
cell is not zero. A value that will not coerce to a number is `#REF!`, not a
guess: thousands separators, parenthesised negatives, and non-ASCII spaces are
refused rather than interpreted.

The evaluator is total, terminating, deterministic and free of input/output.
It reads nothing: not the clock, not the network, not a path.
There is no flag that changes this. Constructs that would read the clock, the
network, or a path are not blocked —
they are unparseable. This is
simultaneously a security property and a correctness one: a content-addressed
cache is silently wrong if a formula can read the clock.

## 9. Refusals — normative

Recognition is total: every byte sequence has exactly one defined outcome, and a
parse error is *reported* separately from being *handled*, so a validator and an
evaluator run the same algorithm and differ only in what they print.

This list is complete. Every refusal the format has is below; a refusal argued
elsewhere in this document appears here too, with a back-reference.

An implementation MUST refuse:

1. conflict markers on any line — a line whose first seven characters
   are seven `<`, seven `=`, seven `>`, or seven `|`, the diff3 base marker
   `|||||||` included (§4.1.12)
2. a duplicate column name
3. a duplicate aggregate name
4. a duplicate `key` or `order` declaration
5. a duplicate row id, where a key is declared
6. a data row whose field count differs from the header
7. an alignment row whose field count differs from the header
8. an alignment-style row among the data rows — a data row *every* cell of which
   is an `align-cell` (§4.1.5)
9. a row-relative operator with no declared order
10. `order := by(c)` where `c` is not a stored column, is computed, mixes types,
    or holds a non-finite spelling (`inf`, `nan`, `infinity`, any case) in any
    row (§6)
11. an unknown aggregate function
12. a malformed declaration — a line containing `:=` that does not match
    `declaration` (§4.1.11)
13. a file containing no table
14. a leading BOM, or bytes that are not well-formed UTF-8 (§3)
15. a lone `CR` (§3)
16. an identifier — column name, aggregate name, `key`/`order` argument, or a
    value of the key column — containing whitespace, a `Cf` format character, or
    any character outside `ident` (§3, §4, §4.1.9)
17. a value in a computed cell (§5)
18. a table line that does not match `table-line`, in particular one lacking its
    closing `|` (§4.1.3)
19. a line that is none of annotation, table line, declaration, or blank —
    including a table line after the table's contiguous run has ended (§4.1.2)
20. a malformed **column formula** — a header cell containing `=` whose
    right-hand side is not a well-formed expression. §9.12 does not reach it:
    that entry is scoped to a line containing `:=`, and a header cell is not one
21. a table whose second line is not a valid alignment row, a table shorter than
    two lines included (§4, §4.1.5)

**The numbering is not a precedence order.** When one file violates several
refusals, *which* is reported is deliberately unspecified, and the three
`parse/two-refusals-*` cases assert only that the file is refused. The reason is
that "exactly one defined outcome" above means one of *accept with these values*
or *refuse* — the identity of the diagnostic is not part of the outcome, and no
value anywhere in the format depends on it. Pinning an order would force every
reader into one detection sequence: a phase reader (bytes, then declarations,
then header, then rows) and a streaming reader that refuses at the first
offending line both refuse the same files, and requiring them to agree on the
message buys nothing and outlaws the streaming reader. What an implementation
MUST be is **deterministic**: the same bytes must yield the same refusal on
every run, or `render` and `canon` are not functions of the input. A conformance
case that asserts on a message substring is therefore a case in which exactly
one refusal applies.

**Reject when degrading could yield a plausible VALUE; preserve and warn when it
could only lose DECORATION.**

Exactly one ignorable channel exists: **a line whose first non-space character
is `#`, outside the table**, plus its inline form on a declaration line
(§4.1.10). It is preserved verbatim by `render` and by `canon`, and it carries an
*inertness promise*: nothing in it may ever contribute to a computed value. That
promise is testable — strip every annotation and assert no value changes.

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

**With a single edition this has no observable behaviour, and that is correct.**
A reader never consults it — interpretation is a function of the artifact's
bytes alone, so there is no "unknown version" case to mishandle. The file exists
now so that a *second* edition does not require retrofitting a mechanism, which
is the failure that cost Python eleven years; it does not exist because
something already needs versioning.

When a second edition exists, these rules apply and none of them is
retrofittable:

- a writer emits only what its edition permits
- artifacts of different editions coexist in one repository with no ceremony
- migration rewrites to the **intersection** — valid under both editions — so
  it is incremental rather than atomic
- escape hatches carry a stated minimum lifetime

A per-file version field is rejected: it would touch every file on a bump, and a
version line at line 1 conflicts with any concurrent edit to the header row.

## 13. Conformance profiles

An implementation may check an ordinary `.csv` against the subset of §9 that a
delimiter-separated file can violate. **That is a different profile, not a
relaxation**, and the difference must be stated rather than discovered:

- refusals 14 (BOM) and 15 (lone CR) are **warnings** in CSV mode. Enforcing
  them would reject 70 of 72 files in one well-maintained public registry on
  first run, and 8 of 20 in another — measured, not estimated.
- refusals covering alignment rows, formulas and aggregates cannot apply,
  because a CSV has none of those constructs.
- **refusal 5 (duplicate row id) requires a sidecar** declaring which column is
  the key. It is the refusal the identity argument exists for, and it is the one
  that costs a file to obtain. Key inference was tried and rejected: a
  legitimately non-unique first column produces confident wrong refusals on
  valid data.

An implementation claiming CSV-mode conformance states which profile it means.


## 14. Conformance suite

`conformance/cases/` holds the suite as directories of real files plus one
`expect.json` each. A conforming implementation runs them against a **stock git
binary**. Merge cases assert on the **evaluated value** of the merged artifact,
not on git's exit code, because a clean merge with a wrong number is the failure
that matters.

An implementation SHOULD also run the mutation gate. A suite that cannot fail a
deliberately broken implementation is measuring nothing.
