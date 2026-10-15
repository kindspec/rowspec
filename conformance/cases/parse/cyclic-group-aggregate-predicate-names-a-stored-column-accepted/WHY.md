# Why this case exists

The control for
`parse/cyclic-group-aggregate-predicate-names-a-computed-column-refused`:
the predicate names the stored column `a` instead of the computed `b`.
§9.22 does not apply, and a cycle is accepted (§4.2 rule 9: such files
"are **accepted files**, not refusals"), so the file is accepted.
`rowrel/cyclic-group-aggregate-with-a-stored-predicate-is-ref-cycle`
asserts the value on the same bytes.
