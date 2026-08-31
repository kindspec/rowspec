<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Why rowspec is shaped this way

The specification says what to do. This says why, so that a future maintainer
who finds a rule inconvenient can see what it cost to learn, and undo it
deliberately rather than by accident.

Every measurement below was run. None is an estimate.

---

## The defect the whole format is organised against

Four failures that looked unrelated turned out to be one:

    an A1 cell reference        insert a row -> a total of 480 where the truth is 660
    a column-alignment row      a renderer silently dropped it
    a block's trailing newline  moving a block defeated its own identity
    a derived coordinate        adding one node moved 4 of 4 others

**Coupled representation: state whose bytes must change when unrelated content
changes.** Coupled state destroys diffs, and a destroyed diff is what makes a
version-controlled artifact pointless.

The rule that follows, and the one every other rule serves:

> **Serialize so that the unit of merge is the unit of meaning.**

Git merges by line. So one line is one row.

## Why names, never positions

Two branches insert a row into a CSV whose formulas use `A1` ranges. Git merges
with **zero conflicts** and the sheet totals **480** where the truth is **660** —
a 27% error with no marker anywhere, confirmed in LibreOffice.

The formal statement is Abiteboul, Hull & Vianu: named and unnamed perspectives
have equal expressive power but different primitive operators. Positional
addressing costs no expressiveness — it costs *cheap correspondence*, which is
exactly what merging is.

And no algorithm rescues it. `daff`, a proper cell-level table merger, merged
the same file's rows *perfectly* and produced the identical wrong answer. **A
structural merger cannot see that a string inside a cell encodes a position.**

## Why correctness cannot depend on a merge driver

`.gitattributes` is tracked and travels. `merge.<name>.driver` lives in
`.git/config` and never does. A fresh clone silently falls back to line merge,
with no warning that a driver was requested and skipped.

Worse, verified directly: **a bare repository does not consult `.gitattributes`
at all** — and a bare repository is what every forge merges in. GitLab
documents that custom merge drivers are unsupported on GitLab.com; GitHub
Support states that GitHub "doesn't consider user-defined .gitattributes
files."

So the expensive, NP-hard, heuristic component turns out to be the one the
design must *not* depend on. That is why correctness lives in the
representation, and why §11 forbids requiring a driver, a filter or a hook.

## Why row order is declared, not implied

A `prev.` operator meaning "the row above" was designed, implemented, and
deleted. "The row above" is a *place*: two branches inserting rows produced a
clean merge in which a row **neither author touched** changed from −273.80 to
218.68.

Declaring the order fixes it, because "the previous row" becomes "the row with
the next-lower key" — a nominal relationship. Physically shuffling every line
then leaves every computed value unchanged, and a backdated row appended last
correctly leads a running total.

The first implementation of that got it wrong in an instructive way: the sort
key was a **string concatenation** rather than a tuple, so a hand-typed
`2026-2-1` sorted after March and an overdraft check read **55.0 where the truth
was 5.0**. Hence §6's insistence on a typed tuple, a mandatory key, and a single
type per ordering column.

## Why the canonical form has no alignment padding

Aligned columns are nicer to read and were the original design. Measured on
2,000 rows, changing one cell from `9` to `1000`:

    padded      2002 added / 2002 removed lines, 238,370 bytes of diff
    canonical      1 added /    1 removed line,      413 bytes

And decisively: two **genuinely disjoint** edits *conflict* when padded and
merge cleanly when canonical. A widening cell reflows every row, so alignment
manufactures conflicts between edits that never touched each other.

The size cost is irrelevant — under gzip padding is +15% — so the diffs were
always the problem, not the bytes.

## Why identifiers reject whitespace and `Cf`

Because two identifiers that render identically must not be able to coexist, or
the duplicate-key refusal never fires. A row keyed ` r_01` and one keyed
`r_01` look the same on every screen and in every diff.

The same reasoning sets §5's trimming rule. Trimming only ASCII space and tab
looks arbitrary until you ask where a non-ASCII space in padding position comes
from: a conforming writer never emits one, so it arrives by paste from a
locale-aware spreadsheet — where it is a **thousands separator**. Trimming it
would silently turn `1 500` into `1500`. The suite refused `1 500` and silently
accepted ` 500`; they come from the same paste.

## Why the conformance suite is the deliverable

There is nearly a controlled experiment for this. CommonMark and djot share an
author; djot is the better language design, written because *"there are 17
principles governing emphasis… and these rules still leave cases undecided."*

    CommonMark   655 executable examples   ~45 implementations, 25+ languages
    djot         no conformance suite      6 implementations, four years in

Same designer, better design, no suite, an order of magnitude fewer
implementations.

But copy the mechanism and fix its defect: CommonMark's own spec concedes that
"not every feature of the HTML samples is mandated", so two implementations at
100% conformance can build different trees. **Testing input→output constrains
one projection of the model, not the model.** rowspec's merge cases therefore
assert on the *evaluated value* of the merged artifact, not on git's exit code.

## Why the suite is not written by the implementer

Three times during design, the same person wrote both a verification artifact
and the thing it verified. Twice the result was a confident claim — "11
namespaces, 0 unprotected" and "15 mutants, 15 killed" — that an independent
adversary then demolished, finding 7 silent-wrong cases and 14 surviving
mutants.

> A verification artifact authored by the implementer measures the
> implementer's imagination.

That is why CONTRIBUTING.md carries it as a hard process rule rather than a
suggestion.

## Why the mutation gate exists, and why staleness is a failure

A suite that cannot fail a deliberately broken implementation is measuring
nothing. The gate proves the suite can fail.

It has twice failed to do that itself, and both failures are the project's own
subject matter:

- **It went stale on a reformat.** Mutants were exact source-text patches;
  `ruff format` invalidated 23 of them, and the gate reported this as a
  harmless note while exiting 0.
- **It counted a kill against a red baseline.** The fixture tree deliberately
  runs ahead of the implementation, so while the reference was failing 15 cases,
  *every* mutant looked killed — including no-ops.

Hence: patterns match a normalised token stream, an ambiguous pattern raises
rather than patching the first hit, a kill is a set difference against an
unmutated baseline, and **a stale mutant exits non-zero**.

    Any tool whose job is to detect a failure must itself fail loudly when it
    cannot run. "Skipped" and "passed" must never share an exit code.

## The pattern this project kept reproducing

Five instances, in five different subsystems:

    1. `#REF!` rendering as zero                          the format
    2. the mutation gate going stale on a reformat        the gate
    3. the gate counting kills against a red baseline     the gate again
    4. `canon = identity` passing a fixture with no runner branch   the runner
    5. git normalising the exact bytes a fixture asserts on         the VCS

Every one is the same shape: **a check that cannot fail, reporting a pass.** In
four of the five, the person who wrote the check was not the person who found it
could not fail.

## The rule that a dogfood run refuted, and why it is worth recording

§4.1.3 once said a cell can never contain `|` "because no escape exists and none
may be invented." It was written as a virtue — an escape is parser complexity
nobody needs — and it was never paid for by evidence.

Replaying 7,446 real commits refuted it in a single number: **26.95% of real
commits were unrepresentable, against a threshold of 2% fixed before any data was
collected, and 95% of those refusals were a pipe inside a value.** The data is
`KS TV | Action`. Ninety-three Ukrainian television channels have a pipe in their
own name, and from 2023-10-16 onward every commit to that file was unwritable.

`\|` is now the sole escape, as it has been in GFM for years. The lesson is not
about pipes: **an elegance that has never met real data is a hypothesis, and this
one was wrong.** Four other thresholds passed in the same run, three of them
comfortably, which is why the failure is credible rather than an artifact.

## The reference implementation borrowed the host language's grammar

§4.2 was written as a normative ABNF and then implemented by calling
`ast.parse`. The grammar in the document and the grammar that ran were two
different grammars, and the difference was invisible until 55,681 real formula
cells were compared against the values the original spreadsheets had cached.

Three defects, one cause:

- **`Nº` and `No` are one column to Python and two to §3.** `ast.parse`
  normalises identifiers NFKC; §3 mandates NFC. In `| Nº | No | out = Nº |`, the
  computed column read `No` and `sum(Nº)` read `Nº` — **one file, one name, two
  answers from two subsystems of the same implementation**, and the
  duplicate-name refusal correctly stayed silent because under NFC the names
  really are distinct. `Nº` is a real header in the corpus.
- **`1000_2999` is a column name that Python reads as the number 10002999**
  (PEP 515 digit separators). §4.2's `literal` is `1*DIGIT [ "." 1*DIGIT ]`, so
  the format had always called this an `ident`. 43 of 8,171 real sheets carry a
  header of this shape.
- **`1e3` and `0x10` are legal `ident`s that Python reads as numbers**, so
  `a*1e3` silently meant `a*1000` while `1e3` in a *cell* was refused as not a
  `number`.

The fix was to write the tokeniser and recursive-descent parser by hand, and to
delete the AST evaluator entirely. Two rules came out of it that the document
had never stated because nothing had forced the question: tokenisation is
**maximal munch over `ident` before anything is classified as a literal**
(`ident` is a strict superset of `literal`, so they are not ordered
alternatives), and identifier equality **must not be delegated to a host
facility whose normalisation has not been checked against §3**.

The independent implementation got all three right, having never had a host
grammar to borrow. That is the whole argument for keeping it.

## A check that cannot fail, reporting a pass — the eighth instance

The conformance runner took its fixture root as the relative path `cases`. Run
from the repository root instead of from `conformance/`, `os.walk` yielded
nothing and the runner printed **`0 failure(s) across the fixture tree`** over
226 cases it had never opened — four of which were failing at the time.

This is the same shape as the seven before it: `#REF!` coerced to zero, the
mutation gate going stale on a reformat, the gate counting kills against a red
baseline, `canon = identity` scoring 129/131, git normalising a CRLF fixture
before any implementation saw it, `check` reporting green on a broken total, and
a group aggregate over a computed column returning 0. **An empty fixture tree is
now a hard failure**, because a suite that has measured nothing must never be
able to say so in the words it uses for success.

## The arithmetic model was left open, and two conforming readers disagreed

§2 filed "number formatting" under *deliberately left open*, which is right for
display and was quietly wrong for the evaluator. Of the cells that agreed with
the cached spreadsheet values only to 15 significant digits, **501 were cells a
40-digit decimal implementation reproduced exactly and binary64 did not** — so a
decimal reader and a binary64 reader were both conformant and disagreed in the
last digit, in a format whose entire claim is that two readers agree. §4.2 now
pins IEEE 754 binary64, and overflow is `#REF!(overflow)` rather than an `inf`
that §4.1.6 would refuse to read back.

## Adding `if` was a measurement, and it moved half as far as the names said

The plan said: close `IF` and `SUM`, they are 17,952 of the 21,165 corpus cells
that translate onto this format's surface and then fall outside §4.2. That
number came from counting function names in a differential run, and it does not
survive reading the expressions those cells actually contain.

**`SUM` was not a missing feature at all.** Of 5,912 corpus cells calling it,
3,485 are `SUM(a, b, c)` over named columns — which is `a + b + c`, already
generated by §4.2 — and 2,376 are `SUM(col)` over a whole column, which is a §7
declaration. 99.1% of them needed no grammar. Adding a variadic row-wise `sum`
would have been a second spelling of `+`, and the format spent §4.1.6 and §4.2
rule 7 refusing second spellings.

What `SUM` was really carrying is that **it skips blanks and `+` does not** —
30.4% of 55,681 compared cells, the largest single disagreement between this
format and real spreadsheets. `if` closes that without a new function and
without changing `+`:

    | t = if(a = "", 0, a) + if(b = "", 0, b) |

which is longer than `SUM(a, b)` and says, in the formula, which cells are
allowed to be missing. A row-wise `sum` would have made blank-skipping the
default and invisible, so a column would quietly under-total the first time
someone left a cell empty. That is I3 either applied or bypassed, and this is
the one place the verbose spelling is the point.

**`IF` was real, and half of it.** 6,640 of 12,697 corpus `if` cells have
numeric branches and one comparison, and those §4.2 now computes. The other
6,057 return **text** — `IF(…, "PASS", "FAIL")` — which is not a grammar
question but a value-model one: a computed column that can hold a string
changes what `sum` over it means, what a `where` predicate compares against,
what canonical form normalises, and what §9.17 checks. Folding that into "add a
function" would have been a way to make the change without ever arguing for it.

Corrected, the two features admit 12,501 of 21,165 rather than 17,952 — 59.1%
of the gap instead of 85%. The interop ceiling moves, and it moves less than
claimed.

The other thing the measurement caught: the first pass scanned raw spreadsheet
formulas and found 798,664 `IF` calls in one corpus, every one of the shape
`IF($C$6<='Apr 2001'!Q12, 'Apr 2001'!A12, 0)`. All of them are cross-sheet
absolute references, none can reach this grammar, and a rule designed against
that frequency would have been designed for formulas that never arrive.
**Function-name frequency is not demand for a grammar.**

## One sentinel for two facts

The first implementation of `if`'s text comparison read a cell with
`env.get(name, "")`. That returns the empty string for a blank cell **and** for
a column that does not exist, and once those two facts share a sentinel no rule
downstream can tell them apart. So:

    if(nope = "", 1, 0)   ->  1.0          on a column that does not exist
    if(nope = 0,  1, 0)   ->  #REF!(nope)  the same operand, one line apart

The same missing column was an error under a numeric comparison and a blank
under a textual one, which is not a policy anybody chose. The consequence is the
worst available: `if(qtyy = "", 0, qty)` — one transposed letter — fires the
missing-data fallback in **every** row, so "use this when that is missing"
silently becomes "always", and `if(regionn = "EU", 1, 0)` matches nothing and
totals zero. §8 says a broken reference never evaluates to zero, empty, or a
stale value; it evaluated to empty.

The fix is `env[name]`, whose `KeyError` *is* the `#REF!`. It is smaller than
the bug.

Two things about how it was found are worth more than the bug itself. It was
found by the conformance author, who is not allowed to read the implementation,
from §8's prose alone — and the first fix for it was **decorative**: an explicit
`if name not in env: raise KeyError(name)` placed above a lookup that already
raised. The mutation gate classified that mutant as *equivalent*, which is the
gate saying the guard cannot fail because it never runs. The mutant that bites
is the one that restores `.get(name, "")`.

## A check that cannot fail, reporting a pass — the tenth instance

The differential harness that produced the corpus figures carries a mutation
control: inject a known defect into the evaluator, re-run everything, and
agreement must collapse. It was keyed on the Python AST node types the
evaluator used before §4.2 was implemented directly. It no longer uses them, so

    RT.OPS[pyast.Add] = operator.sub

installed a dead dictionary key named `Add`, `+` went on adding, and the mutant
would have run the whole differential, reported total agreement, and been read
as *the harness is sound* when it meant *the mutation never fired*. A second
mutant was dead the same way, testing `isinstance(node, ast.Name)` against nodes
that are no longer that type.

Every mutant now asserts that it changed something before the run starts, and
that assertion was itself tested by breaking it — because an arming check that
cannot fail is the same bug one level up.

## The formula ceiling is deliberate, and the cell counts that argue against it are inflated

`.mdtbl` computes arithmetic over named columns, with `if`, comparisons and five
aggregates. Measured against 5,526 real workbooks, that leaves 8,417 corpus
cells it cannot evaluate. The obvious response is to add the functions those
cells name — `ROUND`, `ROUNDDOWN`, `INT`, `MIN`, `MAX`, `CEILING`. Together
those are 4,362 of the 8,417.

They are also **nine distinct expressions**.

    Call:ROUNDDOWN     2,052 cells      1 distinct expression
    Call:ROUND           921 cells      2
    Call:INT             621 cells      2
    Call:MIN             543 cells      2
    Call:CEILING         186 cells      1
    Call:MAX              39 cells      1

`ROUNDDOWN`'s 2,052 cells are one formula — a bowling average — filled down a
column in a problem the corpus ships six times. The mean across those six
functions is **485 cells per distinct expression**.

Two multipliers stack and neither is visible in a function tally: the corpus
replicates each problem about sixfold, and one authored formula occupies every
row of its column. So a single decision by a single person arrives as five
hundred cells.

This is the same finding as the one above about `SUM`, corrected one term
further. There, *function-name frequency is not demand for a grammar*. Here,
**cell frequency is not demand either** — the unit that matters is a distinct
expression, because that is the unit somebody wrote.

Adding a function is not local. It costs normative text with its choices
argued, fixtures written by an author who may not read the implementation,
mutants proving those fixtures bite, and a second implementation built from the
prose alone. That is the right price for a capability and the wrong price for
nine formulas.

The one entry with real breadth is `IF` returning **text** — 2,602 cells across
29 distinct expressions, the widest by an order of magnitude. That is not a
function to add: it changes what a computed value *is*, and reaches §5, §7, §8,
§9.17 and §10's canonical form. §4.2 rule 10 declines it deliberately and says
so. If this ceiling is ever raised, that is the only candidate whose evidence is
breadth rather than replication, and it deserves its own argument.

## What this format deliberately does not do

Domain validation. Whether a country code is in ISO 3166, whether a URL
resolves, whether a date is plausible — none of that is here, and Frictionless
Table Schema does it well. rowspec checks whether a table **survives version
control**, which is a different and much smaller question.

It also does not promise to merge everything correctly. Semantic conflicts —
two authors editing different sentences that must agree — are unfixable by any
representation, and every honest system says so.

And it does not beat plain CSV on a table of facts. In 528 real three-way merges
replayed from public registries, **neither `.mdtbl` nor CSV ever merged silently
wrong.** For a sorted registry with no computed columns, stock git already does
what this format promises. The format earns its keep only where a merge can
leave a *total* quietly wrong — which is a failure a CSV cannot even express,
and which none of those maintainers has had reason to care about in four years.

That is the honest shape of the value: narrow, real, and not yet wanted by
anyone we have measured.

## Credit

Coopy/daff has shipped row-ID-aware, git-integrated CSV three-way merging since
2013. rowspec's mandatory opaque row id is a **deliberate divergence** from its
author's stated reasoning — Coopy chose content-based matching and treated IDs
as an optional optimisation — not an unawareness of it. See NOTICE.
