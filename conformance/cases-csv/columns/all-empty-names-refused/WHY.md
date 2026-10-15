# Why this case exists

Every header name is empty.

§13: "an empty header cell" is a column name, and "a header cell of spaces,
one of a tab and an empty one" are one name, "so any two of them are a
duplicate". Three empty names are a duplicate (§9.2). The data row has the
header's three fields and no sidecar is supplied, so no other refusal of
§13's profile applies.

The CSV tree asserts only that a file is refused, never which refusal
(§13: "its conformance cases assert only that a file is refused"). This
case is built so that §9.2 is the only refusal SPEC.md gives it, but it
does not prove §9.2 is the one that fired: a reader that refused it for
another reason would pass too.
