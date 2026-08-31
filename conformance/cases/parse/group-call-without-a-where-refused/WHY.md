# Why this case exists, and one consequence worth confirming

§4.2's grammar makes the `where` clause mandatory in a header cell:

    group-call = agg-fn "(" *WSP ident 1*WSP "where" 1*WSP predicate *WSP ")"

There is no alternative without a predicate, and `sum(a)` is not an `expr`
either — `primary` is `literal / ident / "(" expr ")"`, none of which matches a
call. So by "Recognition is whole-cell ... or the cell is refused (§9.20)",
`| x = sum(a) |` is refused.

The consequence, which §4.2 does not state anywhere: **a whole-column aggregate
repeated on every row is not expressible as a computed column.** It is
expressible as a table-level aggregate (`s := sum(a)`), which is a different
thing — one value below the table rather than one per row. That may well be
intended, since the per-row form is a column of one repeated number, but it is
a capability decision reached by silence rather than by a [CHOICE].

The reference refuses it, matching the grammar. `rowspec_alt` accepts it and
computes a grand total per row.

## Addendum: what this case does and does not pin (issue #7)

The data rows above carry **two** fields against a three-field header, so the
file is refused under §9.6 (field-count mismatch) no matter how the header
cell is parsed, and `refusal_contains: ""` accepts any refusal reason. An
implementation that wrongly ACCEPTS a header-cell `sum(a)` therefore passes
this case: it never tested its name. It still pins something — the file must
be refused, not repaired — but not the `where`-is-mandatory rule.

Per the ground rules ("add, do not edit") the fixture is left as it is; the
corrected sibling is `parse/group-call-without-a-where-in-header-refused`,
whose only defect is the `where`-less group call itself.
