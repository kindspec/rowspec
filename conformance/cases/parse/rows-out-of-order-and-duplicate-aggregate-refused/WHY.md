# Why this case exists

The rows are out of key order and the aggregate name `n` is declared twice (§9.3).

§9.28: "It is the exception to the rule below that any applicable refusal may be reported: a file that any other entry refuses is reported under that entry, since only this entry is repairable by `canon`, and two rows holding one key are always §9.5".

§9: "Apart from §9.28, when one file violates several refusals, which is reported is deliberately unspecified".

The only identifier is `duplicate-aggregate`, and a reader that reports `rows-out-of-order` fails this case.
