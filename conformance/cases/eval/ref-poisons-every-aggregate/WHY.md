# Why this case's `n` expectation changed

When this case was written it asserted `n = #REF!(amt)` for a column holding
`[10, "1,000", 30]`, on the strength of §8: "An aggregate over any column
containing a `#REF!` is itself `#REF!` — **it must not sum the values it can
read**." The other four aggregates still assert exactly that and still pass.

`count` was carved out of that rule deliberately, and **I was asked to
adjudicate the change and agreed with it.** SPEC §7 now reads: "`count` counts
rows and never coerces. It is poisoned by a `#REF!` actually present in the
column, because that is an error value — but not by a value that merely fails to
parse as a number, because `count` never uses it as an operand."

Three reasons, in the order I weight them.

**1. The suite had already settled it, and the preamble says the suite wins.**
`eval/count-includes-blanks` asserts `count = 2` over a column with a blank
cell. A blank is precisely a value that cannot serve as a numeric operand — §8
says so in the same paragraph, "A blank cell is not zero" — and `count` counts
it anyway. So `count` was already a row-counter that does not inspect values.
Poisoning on `1,000` while not poisoning on a blank is incoherent: both are
"not a number". The new rule makes those two cases agree; the old behaviour did
not, and nobody noticed because nothing counted a non-numeric column.

**2. §4.1.6 already scopes coercion failure to the point of use.** "Refused, and
therefore text — `#REF!` **when used as an arithmetic or aggregate operand**
(§8)." The cell's value is text; it becomes `#REF!` when something uses it as an
operand. `count` never does. The poisoning reading requires ignoring that
clause.

**3. §8's sentence is preserved, not weakened.** A `#REF!` genuinely present in a
column still poisons `count` — see `eval/count-poisoned-by-a-ref-in-the-column`,
added alongside this change precisely so the carve-out cannot drift into "count
never poisons". What changed is which values count as "containing a `#REF!`":
an error value, not any text that fails to parse as a number.

**The argument against, and why it loses.** A column the author plainly intended
as numeric, holding one badly-pasted `1,000`, is a defect, and loud failure is
this format's instinct. True — and the defect is reported four times over, by
`sum`, `min`, `max` and `avg`, all of which are asserted in this very file. A
fifth report from `count` adds no information a reader can act on. Meanwhile the
poisoning reading returns an error for `count` on *every text column in the
format*, including ones where nothing is wrong, which §9 already rejects in
principle: "Refusing is not the same as being strict for its own sake."

The sharpest form: `sum`, `min`, `max` and `avg` are type-committed — applying
one declares numeric intent, so poisoning detects a violated intent. `count` is
type-agnostic. Poisoning it detects nothing; it only refuses to count.
