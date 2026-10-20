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

## Identifier

This case asserts `refusal: "duplicate-declaration"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "a member repeated within one object of the sidecar, and two `columns` members naming one column: §9.4 `duplicate-declaration`."

§9.4: "`duplicate-declaration`: a duplicate `key` or `order` declaration (see §13 for the CSV profile)"

The earlier paragraph on `refusal_contains: ""` describes this case before §13 gave CSV-mode refusals identifiers; it now asserts `duplicate-declaration` instead.
