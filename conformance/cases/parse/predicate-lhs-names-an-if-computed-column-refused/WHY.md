# Why this case exists

§9.22: "an equality in a `where` predicate whose left-hand `ident`, or whose
`ident` after `@`, names a **computed** column (§4.2 rule 5)."

`flag` is computed, and it is computed by an `if` — which is the version of this
refusal an implementation is most likely to miss, because `if` produces exactly
the small integer domain (`1`/`0`, `1`/`2`, a category code) that people write
predicates against. The corpus shape is "flag the rows, then sum by flag", and
it is unwritable in this format.

Rule 5 gives the reason and it applies unchanged here: "Comparison is on the
cell's text (rule 6) and a computed column has no cell text: §5 requires its
data cells empty. The only available reading would compare against the
*rendered* form of a computed number, and §2 deliberately leaves number
formatting to the implementation — so one reader would write `20`, another
`20.00`, and the two would match different rows with no diagnostic on either."

And the failure mode if the refusal does not fire: "A predicate naming a
computed column matches nothing, and `sum` over an empty match set is `0` — a
plausible number, produced by a predicate that could never fire."

§9.22 is semantic, not syntactic — "no grammar can tell a stored column from a
computed one" — so an implementation that added `if` purely in its parser has
nothing that would catch this.
