The sidecar declares `key` and a member `oder`, which §13 does not define.
`id` names a column and its values are unique.

§13: "A member the profile does not define is refused, because a misspelt
`oder` would otherwise switch a check off without a word."

§13: "the sidecar is one JSON object with five optional members: `key`,
`order`, `order_type`, `columns` and `delimiter`."

`oder` is none of the five, so the sidecar is refused. The `o` column holds
two numbers, so had the member been `order` the file would be accepted:
nothing but the undefined member is at fault.

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the undefined member is the only fault in the file and its
sidecar, so a reader that refuses it has refused for that reason or for one
§13 does not give. What the case does not pin is which reason the reader
reports.
