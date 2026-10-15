The sidecar's only member is `Key`, with a capital K. `id` names a column
and its values are unique.

§13: "the sidecar is one JSON object with five optional members: `key`,
`order`, `order_type`, `columns` and `delimiter`."

§13: "A member the profile does not define is refused, because a misspelt
`oder` would otherwise switch a check off without a word."

The member names are written in lower case and nothing in §13 folds case, so
`Key` is not `key`: it is a member the profile does not define, and it is
refused.

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the undefined member is the only fault in the file and its
sidecar, so a reader that refuses it has refused for that reason or for one
§13 does not give. What the case does not pin is which reason the reader
reports. A reader that folds member names to lower case accepts this file.
