# Why this case exists, and the tension it pins

SPEC.md §4.1.6: `number = [ "-" ] 1*DIGIT [ "." 1*DIGIT ]`. `007` and `1.50`
both match, so both are numbers. This case asserts that reading.

It is here because it sits against §4.1.6's own [CHOICE] rationale for the
refusals in the same paragraph:

> "Exponents, a leading `+`, and the one-sided decimal point are refused rather
> than accepted: each is a second spelling of a value that already has one, and
> a second spelling compares equal as a number and unequal as text, which splits
> `where` predicates and key identity from arithmetic."

`007` is a second spelling of `7`, and `1.50` a second spelling of `1.5`, by
exactly that test: equal as numbers, unequal as text. The grammar admits them
and refuses `+5`, so the stated reason does not pick out the set the grammar
picks out. Leading zeros and trailing decimal zeros cannot be refused without
breaking every zero-padded identifier and every currency column written to two
places, which is presumably why they are in — but then the rationale, not the
rule, is what needs amending.

No case is written for the refusal direction, because the grammar determines
acceptance and inventing the opposite is not mine to do. See
`design-findings/M0-adversarial-cases.md`.
