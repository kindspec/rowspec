# Why this case exists

The first two data rows are out of key order. The last data row holds a value in the computed column `b` (§5, §9.17).

§9.28: "It is the exception to the rule below that any applicable refusal may be reported: a file that any other entry refuses is reported under that entry, since only this entry is repairable by `canon`, and two rows holding one key are always §9.5".

§9: "Apart from §9.28, when one file violates several refusals, which is reported is deliberately unspecified".

The only identifier is `value-in-computed-cell`. A reader that stops at the first out-of-order pair and reports `rows-out-of-order` fails this case.
