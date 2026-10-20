The file is a UTF-8 BOM and nothing else. The BOM is a warning; what follows it is empty, so the file has no header row.

## Identifier

This case asserts `refusal: "no-table"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "refusals 26 (`leading-bom`) and 15 (`lone-cr`) are warnings in CSV mode; 14 (`bad-encoding`) is still refused."

§13: "a file with no header row, an empty file included: §9.13 `no-table`."

§13: "A warning, §9.26's and §9.15's included, is not a refusal, and is not checked against the case's identifiers."

§9.13: "`no-table`: a file containing no table"
