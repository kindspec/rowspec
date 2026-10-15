The sidecar is `{}`: a JSON object with no members. The CSV repeats the id
`r1` in its first column.

§13: "the sidecar is one JSON object with five optional members: `key`,
`order`, `order_type`, `columns` and `delimiter`."

Every member is optional, so an object with none is a valid sidecar. It
declares no key, and refusal 5 "requires a sidecar declaring which column is
the key" (§13). Without a declared key §9.5 cannot apply, so the repeated
`r1` is not a duplicate row id and the file is accepted.

A reader that refuses an empty sidecar, or that treats one as declaring the
first column the key, refuses this file.
