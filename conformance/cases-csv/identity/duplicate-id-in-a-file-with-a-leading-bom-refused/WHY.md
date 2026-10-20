The file starts with a BOM, which §13 makes a warning, and the declared key `id` holds `r1` twice.

## Identifier

This case asserts `refusal: "duplicate-row-id"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "refusals 26 (`leading-bom`) and 15 (`lone-cr`) are warnings in CSV mode; 14 (`bad-encoding`) is still refused."

§13: "two rows with one value of the declared key: §9.5 `duplicate-row-id`."

§13: "A warning, §9.26's and §9.15's included, is not a refusal, and is not checked against the case's identifiers."

§9.5: "`duplicate-row-id`: a duplicate row id, where a key is declared"
