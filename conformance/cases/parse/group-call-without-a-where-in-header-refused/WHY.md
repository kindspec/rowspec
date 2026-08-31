# Why this case exists

§4.2's grammar makes `where` mandatory in a header-cell `group-call`:

    group-call = agg-fn "(" *WSP ident 1*WSP "where" 1*WSP predicate *WSP ")"

while §4.1's declaration `arg` makes it optional (`grand := sum(qty)` is
fine). The distinction lives only in those two ABNF blocks — no prose states
it — and getting it wrong is not a refusal bug but a silent capability bug: a
reader that shares one parser between declarations and header cells accepts
`| x = sum(a) |` and computes a per-row grand total in every row.

This is the corrected sibling of `parse/group-call-without-a-where-refused`
(issue #7). That case's data rows carry two fields against a three-field
header, so the file is refused under §9.6 *regardless* of how the header cell
is parsed, and with `refusal_contains: ""` an implementation that wrongly
accepts a header-cell `sum(a)` passes it anyway. Per this tree's ground rules
the original is left untouched; its WHY.md records what it does and does not
pin.

Here every other refusal ground is removed: three fields in every row, blank
computed-column cells, unique row ids, `key := id`, nothing else. The only
thing wrong with the file is `sum(a)` — an aggregate with no `where` — in a
header cell. Verified against a wrapper mutant that swallows exactly the
header-cell refusal: the mutant still passes the original case and fails this
one.
