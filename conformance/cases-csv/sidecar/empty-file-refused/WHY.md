The sidecar file exists and holds zero bytes. The CSV has no fault.

§13: "the sidecar is one JSON object with five optional members: `key`,
`order`, `order_type`, `columns` and `delimiter`."

§13: "So is a sidecar that is not valid JSON, or not an object, and a member
repeated within one object, `columns` included: JSON's last-one-wins is the
silent overwrite §9.4 refuses."

Zero bytes are not a JSON text (RFC 8259 §2: a JSON text is a value), so the
sidecar is not valid JSON and is refused. A reader that treats an empty
sidecar as absent accepts this file.

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the sidecar's not being valid JSON is the only fault in the
file and its sidecar, so a reader that refuses it has refused for that
reason or for one §13 does not give. What the case does not pin is which
reason the reader reports.
