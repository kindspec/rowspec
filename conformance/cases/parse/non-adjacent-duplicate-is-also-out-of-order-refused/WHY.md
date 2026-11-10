# Why this case exists

`r_1` is held by the first and third rows, with `r_2` between them, so the file meets §9.5. The adjacent pair `r_2`, `r_1` is also out of key order.

§9.28: "It is the exception to the rule below that any applicable refusal may be reported: a file that any other entry refuses is reported under that entry, since only this entry is repairable by `canon`, and two rows holding one key are always §9.5".

§9: "Apart from §9.28, when one file violates several refusals, which is reported is deliberately unspecified".

The only identifier is `duplicate-row-id`, and a reader that reports `rows-out-of-order` fails this case.
