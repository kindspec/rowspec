The sidecar holds `columns` twice, each typing `n` as `number`. `n` holds
two numbers, so either `columns` alone would be accepted.

§13: "So is a sidecar that is not valid JSON, or not an object, and a member
repeated within one object, `columns` included: JSON's last-one-wins is the
silent overwrite §9.4 refuses."

"`columns` included" names this member. Two equal objects are still a
repeated member.

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that the repeated member is the only fault in the file and its
sidecar, so a reader that refuses it has refused for that reason or for one
§13 does not give. What the case does not pin is which reason the reader
reports.
