# Why this case exists

§4.2 rule 10: "**Only the selected branch is evaluated.**" The companion to
`rowrel/if-lazy-branch-guards-division-by-zero`, with the *other* error §4.2
rule 2 manufactures out of otherwise-valid operands: "**Overflow is
`#REF!(overflow)`.** An operation whose IEEE result is an infinity does not
store one."

Division by zero is the case every implementer will have read, because rule 10
prints it. Overflow is the same rule and is not printed, so an implementation
that special-cased `/0` — suppressing the divide-by-zero error rather than
declining to perform the division — passes the canonical case and fails this
one. That distinction is the whole point of writing both: laziness is *not
performing the operation*, not *catching what it raises*.

**Overflow is a data fault, and this case is the third member of that family.**
§4.2 rule 10 draws its line between the header and the data: an unresolved name
is a property of the header and is `#REF!(name)` in every row, while "whether
`b` is zero in `if(c > 0, a / b, 0)` is a property of the data, so `#REF!(/0)`
is legitimately a per-row answer and this rule does not touch it." Whether
`big * big` overflows depends on what is in the `big` cell — an edit to that one
cell changes the answer — so overflow sits with `/0` on the data side, and this
case must stay `1.0` however static the treatment of unresolved names becomes.

The family, all on the same shape and all asserted in the row that does *not*
select the faulty branch:

    | x = if(c > 0, c * 2, nope)      |  header  ->  #REF!(nope) in every row
    | x = if(c > 0, c * 2, a / z)     |  data    ->  the good branch's value
    | x = if(c > 0, 1, big * big)     |  data    ->  the good branch's value

`rowrel/if-unselected-branch-naming-a-missing-column-is-static` and
`rowrel/if-unselected-branch-dividing-by-zero-stays-per-row` are the first two.
An implementation that hoists every branch fault to the whole column passes the
first and fails the other two.

`rowrel/if-overflow-in-the-selected-branch` is this case's own mirror, on the
same operands with the branches swapped, and that pair is what separates
laziness from error-suppression: an implementation that evaluates both branches
and discards the loser passes the mirror and fails this one; one that catches
and swallows overflow passes this one and fails the mirror.

§8 counts `#REF!(overflow)` among its shapes as of the amendment that made the
count **four**; when this case was written the paragraph said *three* and did
not name it, while rule 2 already required it.
