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
cell        = *( escaped / ( char - "|" ) )
escaped     = "\" "|"                        ; the sole escape
;   `cell` is AMBIGUOUS as written -- `char` includes "\", so `\|` parses
;   either as `escaped` or as a literal "\" ending the cell. The split is
;   NORMATIVELY on unescaped pipes: `escaped` wins. The two readings give
;   different FIELD COUNTS, which is the exact harm rule 3 exists to prevent.
;   A backslash not followed by "|" is a literal backslash.
declaration = *WSP ident *WSP ":=" *WSP rhs [ 1*WSP "#" *char ] eol
rhs         = ident "(" *WSP arg *WSP ")" / ident
arg         = ident [ 1*WSP "where" 1*WSP predicate ]      ; predicate: §4.2
ident       = 1*( LETTER / MARK / NUM / "_" )
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

**3. The pipe.** Both the leading and the closing `|` are required. A cell may
contain a pipe **only** as `\|`, and that is the format's sole escape. A reader splits a
**table line** on unescaped pipes and unescapes `\|` in each cell; a writer
escapes every literal `|` it emits **into a table line**.

Both halves are scoped to the table line, and the scoping is load-bearing. A
declaration line is never unescaped, so the same string has two spellings
depending on which line it sits on:

    g := sum(amt where region = "KS TV | Action")       declaration: raw
    | t = sum(amt where region = "KS TV \| Action") |   header cell: escaped

Getting this wrong is silent: the escaped spelling in a declaration matches zero
rows and reports `0`. No other escape exists and none may be
invented — `||`, a quoted cell, a doubled delimiter — because an unrecognised
escape makes a file whose field count differs between readers, so one sees the
row the author wrote and the other sees an extra field or a truncated value.

**[CHOICE], and a reversal.** An earlier draft admitted no escape at all, on the
reasoning that an escape is parser complexity nobody needs. That was never paid
for by evidence, and a replay of 7,446 real commits refuted it: **26.95% of real
commits were unrepresentable, 95% of those because a value contained a pipe.**
Ninety-three television channels in one public registry have a pipe in their own
name, and from 2023-10-16 onward every single commit to that file was
unwritable. The rule was elegant and the data did not care. **[CHOICE]**
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
letters, marks or digits, or `_`. Whitespace and `Cf` are excluded by
construction, which is what §3 and §4 require; so are `|`, `=`, `:`, `#`, `(`,
`)`, `,`, `"` and `@`, each of which is structural somewhere — a column named
`total (USD)` would be unquotable inside a formula, and `#` would be
indistinguishable from an annotation.

**[CHOICE]** The set is an allowlist rather than a denylist so that the answer
for a character nobody has thought of yet is *refused*, not *whatever this
implementation's punctuation table happens to say*.

**[CHOICE]** `-` and `.` are excluded, though an earlier draft admitted them.
The formula language uses `-` as subtraction, so a column named `a-b` would be
well-formed and permanently unreferenceable, and two readers would silently
total different columns. The cost is the ability to name a column `a-b`.

**10. Annotations.** Two forms, and only two. A whole-line annotation is a line
whose first non-`WSP` character is `#`, outside the table; everything after the
`#` is inert, whatever it looks like — `# key := id` is an annotation, not a
malformed declaration, because commenting a declaration out is the reason the
channel exists. An inline annotation is `WSP` followed by `#` to end of line, on
a **declaration line only**; `g := sum(v)# note` has no whitespace before the
`#` and is a malformed declaration. **`#` inside a table line is data**, never
an annotation: cells legitimately hold `#4`, `#widget` and `#ff8800`, there is
only one escape and it is for the pipe (rule 3), and an inline channel inside
the table would make those values unwritable while silently truncating the rows
that contain them.

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

### 4.2 Expression grammar — normative

The language every computed column (§5) and every table-level aggregate (§7) is
written in. §4.1 fixed `ident` without fixing the language `ident` is used in,
and an independent implementer working from this document reported that the
architecture transmitted and the surface syntax did not: after §4.1 landed, the
behaviours they had to guess dropped from seven to one, and every defect that
survived was in this language. Same conventions as §4.1, including **[CHOICE]**
for a decision rather than a description of settled behaviour.

`number`, `ident`, `char`, `DIGIT` and `WSP` are §4.1's. `DQUOTE` is U+0022.

```abnf
formula     = call / expr          ; a header cell's right-hand side, entire
call        = rowrel-call / group-call
rowrel-call = rowrel-fn "(" *WSP ident *WSP ")"
group-call  = agg-fn "(" *WSP ident 1*WSP "where" 1*WSP predicate *WSP ")"
rowrel-fn   = "cumulative" / "prior" / "delta"
agg-fn      = "sum" / "count" / "min" / "max" / "avg"

expr        = term *( *WSP ( "+" / "-" ) *WSP term )
term        = factor *( *WSP ( "*" / "/" ) *WSP factor )
factor      = [ "-" *WSP ] primary
primary     = literal / ident / "(" *WSP expr *WSP ")"
literal     = 1*DIGIT [ "." 1*DIGIT ]        ; unsigned -- rule 7

predicate   = equality *( 1*WSP "and" 1*WSP equality )
equality    = ident *WSP "=" *WSP pred-rhs
pred-rhs    = string / at-ref                ; at-ref: header cells only, rule 5
at-ref      = "@" ident
string      = DQUOTE *( char - DQUOTE ) DQUOTE
```

A declaration's right-hand side is §4.1's `rhs`, whose `arg` carries the same
`predicate` — with `at-ref` removed (rule 5). A declaration is never an `expr`:
`g := sum(qty) * 2` is a malformed declaration (§9.12), not an expression over
an aggregate, because `rhs` has no arithmetic alternative and none is added
here.

**Recognition is whole-cell.** A header cell's right-hand side matches one
alternative of `formula` in its entirety or the cell is refused (§9.20); a
declaration's right-hand side matches `rhs` in its entirety or the line is
refused (§9.12). There is no
partial parse and no fallback to text: §4's rule that a reader which cannot
recognise a construct MUST NOT degrade a failed recognition into a different
successful one applies here with particular force, because the successful
reading available to a lazy implementation is "treat the cell as a plain column
name", which turns a broken formula into a stored column of blanks.

**1. Operators.** Binary `+`, `-`, `*`, `/`, and unary `-`. That is the whole
set. Precedence, tightest first: parentheses; unary `-`; `*` and `/`; `+` and
`-`. Binary operators are **left-associative**, so `8 - 4 - 2` is `2` and
`8 / 4 / 2` is `1`. Unary `-` binds tighter than any binary operator, so
`-a + b` is `(-a) + b`.

**[CHOICE]** `**`, `^`, `%`, `//`, `&`, `|`, `<<`, `>>`, `~`, the comparison
operators (`<`, `>`, `<=`, `>=`, `==`, `!=`, `<>`), and the words `or` and `not`
are **refused** rather than given a meaning. `^` is the case that decides the
policy: it is exponentiation in Excel, Sheets, Lotus and every spreadsheet the
users of this format have met, and bitwise XOR in C, Python, Java and Go. Both
readings are total functions over numbers, neither raises, and `3 ^ 2` is `9`
under one and `1` under the other — the same file, two totals, no diagnostic.
There is no reading of `^` that two implementations arrive at by accident, so
the format has none. `%` (modulo in C, percent-of in a spreadsheet) and `//`
(floor division in Python, a line comment in C and SQL) fail the identical test.
`**` fails a weaker one: it has a single agreed meaning, and it is a capability
this format does not have. Adding it is a proposal, not a clarification.

The list above is not the rule. **The rule is that `expr` is exactly what the
ABNF generates**, and an operator character appearing anywhere else refuses the
formula. Stating the list separately would invite an implementation to reject
the named operators and accept the twentieth one nobody wrote down.

**2. Arithmetic is IEEE 754 binary64.** **[CHOICE]** Every operand is converted
to a binary64 double and every operator is the corresponding IEEE 754 operation
under round-to-nearest-even. This was left open once and should not have been:
measured against a corpus of cached spreadsheet results, 501 cells were ones a
40-digit decimal implementation reproduced exactly and binary64 did not — so a
decimal reader and a binary64 reader were both conformant and disagreed in the
last digit, which is a silent cross-implementation divergence in a format whose
entire claim is that two readers agree.

Binary64 rather than decimal, on the format's own terms: it is what every host
language's default arithmetic already is, so a conforming implementation is the
path of least resistance rather than a library dependency; and decimal is not
one choice but three — precision, rounding mode, and when to round — each of
which would need pinning here and none of which has an answer that is obviously
right. Matching any particular spreadsheet's last digit is explicitly **not** a
goal (§1); agreement between conforming implementations is.

**Overflow is `#REF!(overflow)`.** An operation whose IEEE result is an infinity
does not store one. The reasoning is rule 2's below, unchanged: `inf` is not a
`number` under §4.1.6, so a file that stored one could not be re-read by the
implementation that wrote it, and `canon` would not round-trip its own output.
`NaN` cannot arise — the only operations that produce it need an infinity or a
zero-divided-by-zero, and both are already error values.

**Division.** `/` is real division: `7 / 2` is `3.5`, never `3`.
**[CHOICE]** — the alternative, integer division when both operands happen to be
integral, makes `qty / 2` depend on whether a cell is spelled `7` or `7.0`, and
§4.1.6 refused a second spelling of a number precisely so that no value in the
format can depend on that.

**Division by zero evaluates to `#REF!(/0)`** (§8). It is an error value and
propagates like any other: the row's cell is `#REF!(/0)` and every aggregate
over that column is `#REF!` too. **[CHOICE]**, against two alternatives, and
each is wrong for its own reason. It is *not a refusal*, because the divisor is
data: a file valid today would become refused when one cell is edited to `0`,
and a validity that turns on a cell's value belongs to §8's error model rather
than to §9's list of things about a file's shape. It is *not `inf` or `nan`*,
because §4.1.6 refuses those spellings as cell values and §9.10 refuses them in
an order column — producing one would manufacture a value the format cannot
store, so `canon` could not round-trip its own output. `/0` is not an `ident`
(§4.1.9 excludes `/`), so `#REF!(/0)` can never be read as a broken reference to
a column.

**3. A call is the whole formula or nothing.** `cumulative(a) * 2`,
`sum(a where b = "x") + 1` and `prior(a) - a` are refused. A `call` never
appears as a `primary`, and `expr` has no call alternative — the two
alternatives of `formula` do not compose. **[CHOICE]** Arithmetic over a
row-relative or grouped result is a capability the format does not have, and
refusing it is the only safe way not to have it. The alternative is measured,
not hypothetical: handed `| x = cumulative(a) * 2 |` under a declared order, the
reference implementation matches neither the row-relative shape nor an
arithmetic one, leaves every `x` cell blank, and reports `0` for `sum(x)`. A
plausible zero is the failure §1 exists to prevent. A refusal is not.

The composition is available by writing the intermediate column down:
`| run = cumulative(a) | twice = run * 2 |` is two well-formed formulas, and by
rule 9 their order in the header does not matter.

**4. The function names are not reserved words.** The eight names of `rowrel-fn`
and `agg-fn` are recognised **only** immediately before `(`, with no `WSP`
between the two. So `| x = sum |` is a reference to a column named `sum`, `sum`
is a legal column name, and `sum (a where b = "x")` — with a space — is refused.
The no-space rule is §4.1's: `rhs` is written `ident "("` with no `*WSP` between
them, and a header-cell call spells its calls the same way. **[CHOICE]** —
reserving eight ordinary nouns would refuse a table with a column named `count`
or `min`, which is an ordinary table, and the format gains nothing for it: a
name before `(` that is in neither list is an unknown function (§9.11), and a
name not before `(` is a column reference, and no third case exists. A name
before `(` that is a `rowrel-fn` with no declared order is §9.9.

**5. `@` is legal in exactly one place: the right-hand side of an equality
inside a `where` predicate in a header cell.** Not in arithmetic, not on a
declaration line, and not in the left-hand side of an equality.

*Not in arithmetic*, because in a header-cell formula a bare `ident` already
means this row's value of that column. `@c` there would be a second spelling of
`c`, and §4.1.6's objection to a second spelling applies unchanged. `@` exists
only because inside a `where` clause a bare `c` means the **candidate** row's
value, so without `@` there would be no way to say *this* row's.

*Not on a declaration line*, because a table-level aggregate has no current row
for `@` to refer to. Any reading an implementation invents — and the reference
implementation invents one, comparing each candidate row against itself — makes
the predicate a filter the author did not write. `g := sum(amt where r = @s)` is
a malformed declaration (§9.12).

**The binding rule, which is the most dangerous thing in this section.** In
`region_total = sum(amount where region = @region)`, the `@` references are
bound **once, to the row whose cell is being computed**, and held fixed while
the aggregated column is scanned over **every** row of the table. The wrong
alternative binds `@region` to the candidate row, which makes every equality
`region = region`, trivially true, and turns every group aggregate into a grand
total. That is a plausible number in every cell and an error in none — a reader
sees `1000` where the truth is `40` and has nothing to notice.

**Both `ident`s of an equality — the left-hand one and the one after `@` — must
name a stored column**, never a computed one. **[CHOICE]** Comparison is on the
cell's text (rule 6) and a computed column has no cell text: §5 requires its
data cells empty. The only available reading would compare against the
*rendered* form of a computed number, and §2 deliberately leaves number
formatting to the implementation — so one reader would write `20`, another
`20.00`, and the two would match different rows with no diagnostic on either.
The outcome is **refusal** (§9.22), not a value. A predicate naming a computed
column matches nothing, and `sum` over an empty match set is `0` — a plausible
number, produced by a predicate that could never fire. That is the same shape as
the binding error above, and §8's "never evaluates to zero" does not catch it:
the empty match set is the symptom, and an empty `sum` is legitimately `0`.

The aggregated column itself carries no such restriction:
`sum(total where region = @region)` over a computed `total` is well-formed and
rule 9 gives it a value.

**6. String literals.** `string` is a double-quoted run of characters that
**may not contain `"`**, and there is no escape inside it. The consequence,
stated rather than discovered: a value containing `"` cannot be matched by a
predicate. **[CHOICE]** — inventing an escape here would be a second escape in
a format that has exactly one (§4.1.3), and §4.1.3's reason carries over
verbatim: an unrecognised escape makes a string whose extent differs between
readers. `'single quotes'` are refused for the same reason `+1` is refused as a
number: a second spelling of a value that already has one.

**§4.1.3's `\|` does not reach inside a string literal, and cannot.** Unescaping
happens when the *table line* is split into cells, before any formula is looked
at, so a header cell's formula is already unescaped by the time this grammar
applies. The consequence is that one logical string has two spellings decided by
which line the formula sits on:

    | t = sum(amt where region = "KS TV \| Action") |    header cell: escaped
    g := sum(amt where region = "KS TV | Action")        declaration: raw

Both appear in the fixture tree and both must match a data cell written
`KS TV \| Action`. Getting it backwards is silent: the predicate matches zero
rows and reports `0`.

**Equality compares text, never numbers.** The comparison is between the
candidate row's cell value — trimmed and unescaped per §4.1.3 and §4.1.4, NFC
per §3 — and the literal's characters, or, for an `at-ref`, the current row's
cell value under the same treatment. So `where qty = "3"` matches a cell holding
`3` and not one holding `3.0`. **[CHOICE]** — numeric comparison would make
those two cells match, and §4.1.6 already argued the general case: a second
spelling that compares equal as a number and unequal as text splits `where`
predicates from key identity. A predicate is grouping, and grouping is identity.

**7. A bare numeric token: the position decides, and the position is fixed by
the grammar.** `123` is a well-formed `ident` (§4.1.9 admits `Nd`), so a column
may be named `123`, and `123` is also a well-formed `literal`. Two positions
exist and each admits exactly one of them:

- **Name positions** — the `ident` argument of `rowrel-call` and `group-call`,
  §4.1's `arg`, either `ident` of an `equality`, and the argument of `key` and
  `order` — admit `ident` and have **no literal alternative**. `sum(123)` is the
  column named `123`. So is `sum(1)`.
- **Operand position** — `primary` — tries `literal` first, so a token matching
  `literal` is a number. `| c = 123 * 2 |` is `246`, and `| c = 123 |` is the
  number `123`, not the column.

**Tokenisation is maximal munch over `ident`, and it happens BEFORE anything is
classified as a literal.** `ident` is a strict *superset* of `literal`, so the
two are not alternatives a tokeniser may try in order: `1000_2999` is one
`ident` token, never the literal `1000` followed by `_2999`. Only a token that
is *entirely* `1*DIGIT [ "." 1*DIGIT ]` is ambiguous, and only that one is
resolved by position above. This is not hypothetical — measured against 8,171
real spreadsheet headers, 43 carry a name of this shape (`10_15` for a time of
day, `1_0` for a version, `31_03_2021` for a date, `1000_2999` for an amount
band), and a host language that reads `1000_2999` as a digit-separated number
returned `10002999` from a formula and the column's real total from `sum` — one
file, one name, two answers.

**Identifiers are compared under NFC (§3), never NFKC.** A host language that
normalises identifiers more aggressively than §3 does will fold two names §3
keeps distinct, and the duplicate-name refusal (§9) correctly does not fire
because under NFC they *are* distinct. `Nº` and `No` are the measured pair, and
`Nº` is a real corpus header: the fold made the formula read one column and the
aggregate over the same name read the other, with no diagnostic on either. An
implementation MUST NOT delegate identifier equality to a host facility whose
normalisation it has not checked against §3.

The cost is stated rather than hidden: **a column whose name matches `literal`
is unreachable from arithmetic.** It remains reachable from every name position,
which is where a machine-generated numeric column name would be used.

**[CHOICE]**, and the alternative is the one every implementer reaches for
first: *resolve a bare numeric token to the column if such a column exists, and
to a literal otherwise*. That is refused because it makes the grammar a function
of the table it is parsing. Under it, adding a column named `2` to a header
silently changes `qty * 2` from doubling to a reference, in a diff that touches
only the header line and never the formula; and the same formula in two files
means two different things. A grammar that cannot be read without the header is
not a grammar.

**`sum(1)` is `#REF!(1)`** — a broken reference to a column named `1`, under
§8's ordinary rule for a name that does not exist. It is almost certainly a typo
and the format still does not refuse it, for a reason that is worth stating
because it looks like an oversight: `sum(nope)` is `#REF!(nope)` and `1` is a
name like any other, so refusing this one would mean refusing an aggregate over
any absent column — which contradicts the fixtures that pin `#REF!` as the
answer, and would make a formula's *acceptance* depend on the header rather than
on its own bytes. **[CHOICE]** The loudness that is available instead is in the
error value: `#REF!(1)` names the thing that was not found, and a reader who
meant the number sees the digit they typed inside a broken reference.

**A `factor` carries at most one unary minus.** `factor = [ "-" *WSP ] primary`,
the bracket is zero-or-one, and `-a` is not a `primary` — so `--a` and `- -a`
are not generated by `formula` and are refused (§9.20). Double negation has an
obvious arithmetic reading, which is exactly why it is worth refusing rather
than accepting silently: it is far more often a typo, a stray character from a
merge, or a `-` that lost its operand than it is an author asking for the
identity function.

**8. Whitespace.** `WSP` — ASCII space and horizontal tab, §4.1's definition —
is permitted between any two tokens of an `expr` and is never required there;
`qty*unit`, `qty * unit` and `qty  *  unit` are one formula. A formula cannot
contain a line break, because it lives inside a cell or a declaration line and
neither survives one (§4.1.1).

Three places where whitespace is **not** optional, all for the same reason —
the token beside it is `ident`-shaped, so without a separator it would lex into
the neighbouring name:

- `1*WSP` on both sides of `where`, or `sum(awhereb = "x")` names a column
  `awhereb`;
- `1*WSP` on both sides of `and`, so `b = "x"and c = "y"` is refused;
- **no** `WSP` between a function name and its `(` (rule 4).

`#` is not whitespace and is not a comment inside a formula. §4.1.10 is
categorical that `#` inside a table line is data, so `| x = a * 2 #note |` has a
formula of `a * 2 #note`, which `formula` does not generate, and the header cell
is refused under §9.20. An implementation that borrows a host language's parser
will silently read `#note` as a comment and accept the file; that is the
mechanism, and it is why this sentence exists.

**9. Evaluation order, forward references, and cycles.** A formula may name any
column, stored or computed, wherever that column stands in the header. **The
order of columns in the header is not an input to any value**, exactly as §6
says a row's position in the file is not.

The wrong alternative is left-to-right evaluation, and it is wrong in a way that
is easy to miss because it produces answers. Under it,
`| net = qty * unit | gross = net * 1.2 |` is a pair of numbers while the same
two columns written in the other order gives `gross` as `#REF!(net)` — so the
header's column order becomes a coordinate, and moving a column, which §10's
canonical form otherwise treats as a pure rearrangement, changes a total.

Evaluation is therefore by **dependency**: a formula's operands are the values
those columns themselves evaluate to. Where the dependency graph is acyclic
every column has exactly one value, and every reader that respects dependencies
computes it, whatever order it visits the header in. This is what makes an
implementation's evaluation strategy — a fixpoint, a topological sort, a lazy
memo — a free choice rather than an interoperability hazard.

**A cycle evaluates to `#REF!(cycle)`**, in every column on the cycle and in
every column whose formula depends, directly or transitively, on one.
`| x = y | y = x |` and `| b = b + a |` are **accepted files**, not refusals —
the fixture tree requires it, and the reason it should is that a cycle is a
property of the whole header rather than of any one cell, so refusing would mean
one author's new column can invalidate another author's line, in a merge where
both lines are individually fine. §8's evaluator stays total and terminating
because the answer is a value.

**[CHOICE]** `#REF!(cycle)` is spelled exactly as a broken reference to a column
named `cycle` would be. The collision is accepted rather than dodged with a
spelling outside `ident`, as `#REF!(/0)` uses: both readings are error values,
both poison every aggregate over the column identically under §8, and no
computed value anywhere branches on which of the two it is. The collision costs
a diagnostic and never a number, and closing it would change the output of a
conforming implementation for no gain.

## 5. Columns

A header cell is a NAME, or a name and a formula separated by `=`:

    | id | item | qty | unit | total = qty * unit |

**The split is at the cell's first `=`.** `=` is outside `ident` (§4.1.9), so
the first `=` can only be the separator, and every later one belongs to a
predicate: in `| t = sum(amt where region = "EU") |` the name is `t` and the
formula is everything after the first `=`, trimmed. The formula's grammar is
§4.2; a header cell containing `=` whose right-hand side that grammar does not
generate is refused (§9.20).

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

The predicate is a conjunction of equalities against a string literal or an
`@` reference. This is the nominal form of `SUMIF`/`SUMIFS`. **§4.2 is the
grammar of everything in this section** — the operator set, where `@` is legal,
what the `@` references are bound to while the aggregated column is scanned,
what a string literal may contain, and what a bare numeric token means in each
position. Read it before implementing this one.

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

**`count` counts rows and never coerces.** It is poisoned by a `#REF!` actually
present in the column, because that is an error value — but not by a value that
merely fails to parse as a number, because `count` never uses it as an operand.
Without this, `count` can never count a text column, which is surprising for a
counting function and follows from nothing anyone intended.

The other four coerce, so for them a value that is not a number is `#REF!` under
§8, and one bad cell poisons the aggregate rather than being skipped.

The distinction is not arbitrary. `sum`, `min`, `max` and `avg` are
**type-committed**: applying one *declares* numeric intent, so poisoning detects
an intent the data violates. `count` is **type-agnostic** — poisoning it detects
nothing, it only refuses to count. And the format had already committed to this
elsewhere without noticing: `count` counts a blank cell, and a blank is exactly a
value that cannot serve as a numeric operand. Poisoning on `1,000` while
counting a blank was incoherent.

## 8. Errors propagate; they never degrade

A reference to a name that does not exist evaluates to `#REF!(name)`. An
aggregate over any column containing a `#REF!` is itself `#REF!` — **it must not
sum the values it can read**.

**There are exactly three `#REF!` shapes**, and an implementation emits no
fourth. `#REF!(name)` carries the *originating* name — the column that could not
be resolved or whose value would not coerce, not the column the error surfaces
in. `#REF!(/0)` is division by zero (§4.2 rule 2). `#REF!(cycle)` is a cycle
among computed columns (§4.2 rule 9). All three are values, all three propagate
identically, and none of them is ever a number.

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
    right-hand side is not generated by §4.2's `formula`. §9.12 does not reach
    it: that entry is scoped to a line containing `:=`, and a header cell is not
    one. This covers an unlisted operator, a call composed into arithmetic, an
    `@` outside a predicate, a string literal outside a predicate, and a `#`
    inside a formula (§4.2 rules 1, 3, 5, 6, 8)
21. a table whose second line is not a valid alignment row, a table shorter than
    two lines included (§4, §4.1.5)
22. an equality in a `where` predicate whose left-hand `ident`, or whose `ident`
    after `@`, names a **computed** column (§4.2 rule 5). §9.20 cannot reach
    this one: that entry is scoped to a right-hand side the grammar does not
    generate, and this constraint is semantic — no grammar can tell a stored
    column from a computed one
23. an `expr` nesting parentheses more than **64** deep (§4.2 rule 1). The
    number is here, rather than left to the implementation, because `primary`
    is recursive with no bound: a reader whose limit is its host's call stack
    accepts at 230 and crashes at 250, and two such readers refuse different
    files for reasons neither documents. 64 is Excel's own nesting limit, so
    the number is one the lineage already carries; no formula written by a
    person approaches it, and a generator or a hostile commit that exceeds it
    gets a refusal rather than a traceback — §8's totality is a security
    property as well as a correctness one

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
