The sidecar holds `order` twice, both times naming `o`. `o` holds two
numbers and `id` two distinct ids, so either `order` alone would be
accepted.

§13: "So is a sidecar that is not valid JSON, or not an object, and a member
repeated within one object, `columns` included: JSON's last-one-wins is the
silent overwrite §9.4 refuses."

The rule is on the repetition, not on a disagreement between the values: two
equal members are still a member repeated within one object. A reader whose
JSON parser keeps the last member sees one `order` and accepts.

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the repeated member is the only fault in the file and its
sidecar, so a reader that refuses it has refused for that reason or for one
§13 does not give. What the case does not pin is which reason the reader
reports.
