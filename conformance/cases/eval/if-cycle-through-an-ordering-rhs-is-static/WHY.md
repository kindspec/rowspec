# Why this case exists

§4.2 rule 10: "**Dependency and cycle analysis is over the whole formula, both
branches included, and is not affected by which branch a row selects.**"

The phrase is "the whole formula". A `cond` has three parts — a `comparison` and
two `expr`s — and the sentence's emphasis falls on "both branches included"
because the branches are the *new* thing `if` contributes. That emphasis is
where an implementation goes wrong: it reads the sentence as an instruction
about branches, walks the two `expr`s to collect dependencies, and never walks
the `comparison`, because a comparison is "not an expression and has no value"
(rule 10's own words, two paragraphs earlier) and so does not look like a place
values come from.

But rule 9 defines a dependency by what a formula *names*: "A formula may name
any column, stored or computed, wherever that column stands in the header ...
Evaluation is therefore by **dependency**: a formula's operands are the values
those columns themselves evaluate to." The `ident` in a `comparison` names a
column and the evaluator reads that column's value. It is a dependency by the
only definition the document gives.

The companion to `eval/if-cycle-through-a-comparison-lhs-is-static`, with the
edge on the **right** of the operator instead of the left. `order-rhs = literal
/ ident`, so an ordering comparison has two `ident` positions and both name
columns; `parse/if-ordering-with-a-column-rhs-accepted` pins that the position
exists at all, and this case pins that a name in it is a dependency.

The two halves are separate cases because they are separate lines of code. An
implementation that collects dependencies from a comparison at all will almost
certainly collect the left-hand `ident`, since that one is mandatory and is what
`comparison` begins with; the right-hand one is optional, is shared with a
`literal` alternative, and is easy to skip on the way past. §9.24 removes the
matching position from `eq-op` — `eq-rhs = string / literal` — so this is the
only place in the format where a column name appears to the right of a
comparison operator, and it has exactly one case guarding it: this one.

**Why this shape and not a simpler one.** A cycle a column closes on *itself* —
`| x = if(x > 0, 1, 0) |` — does not test this, because an evaluator catches it
by noticing re-entry into the cell it is already computing, with no dependency
graph involved at all. A cycle that closes through a *second* column can only be
found by the graph, so it is the shape that distinguishes an implementation
whose graph includes the comparison's names from one whose graph does not.

Nor does a non-cyclic forward reference test it: see
`rowrel/if-comparison-names-a-forward-computed-column`, which pins rule 9's
ordering guarantee and explains why it cannot separate the two implementations.

The wrong answer is not a refusal and not `#REF!(cycle)`. With the edge missing,
the graph is acyclic, the columns get evaluated in some order, and each one
yields whatever the other happened to hold at the time — a number, or a
`#REF!(name)` naming a column that exists. §8 reserves the name shape for "the
column that could not be resolved or whose value would not coerce", and a reader
handed `#REF!(y)` for a cyclic header cannot tell it from a missing column
called `y`. Rule 9 chose the third shape precisely so that a cycle is
identifiable: `#REF!(cycle)`.
