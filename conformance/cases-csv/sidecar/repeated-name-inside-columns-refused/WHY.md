The sidecar's `columns` object holds the member `n` twice, both `number`.
`n` holds two numbers.

§13: "So is a sidecar that is not valid JSON, or not an object, and a member
repeated within one object, `columns` included: JSON's last-one-wins is the
silent overwrite §9.4 refuses."

The repetition is "within one object", and `columns` is an object, so a
member repeated inside it is refused as one repeated at the top level is.
§13 says so of `columns` directly too: "Two members naming one column ...
are refused as a repeated member is."

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the repeated member is the only fault in the file and its
sidecar, so a reader that refuses it has refused for that reason or for one
§13 does not give. What the case does not pin is which reason the reader
reports.
