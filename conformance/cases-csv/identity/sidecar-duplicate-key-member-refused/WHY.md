The sidecar declares `key` twice. Both named columns exist and both hold
unique values, so the only fault is the repeated declaration. Reading:
§9.4 refuses a duplicate `key` declaration, and the sidecar is the CSV's
only place to declare one. JSON parsers disagree on duplicate members
(RFC 8259 calls the behaviour unpredictable), so two readers would key on
different columns, which is the divergence §2 forbids.

## Identifier

This case asserts `refusal: "duplicate-declaration"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "a member repeated within one object of the sidecar, and two `columns` members naming one column: §9.4 `duplicate-declaration`."

§9.4: "`duplicate-declaration`: a duplicate `key` or `order` declaration (see §13 for the CSV profile)"

Either value of `key` names a column whose values are unique, so whichever a reader keeps, no other refusal applies.
