# Why this case exists

§8: "**A name in the predicate that does not resolve is `#REF!(name)`, not a
refusal.**" — and this case is the "not a refusal" half, pinned on its own.

`eval/predicate-missing-column-is-ref-not-zero` asserts the value over these
same bytes, but a value assertion can only run if the file is accepted first:
an implementation that refuses here — the divergence this rule exists to
remove — fails that case with a refusal message rather than a wrong value,
which reads as a crash, not as the disagreement it is. This case states the
acceptance directly.

§8's ground is §4.2 rule 7's, carried over unchanged: refusing "would make a
formula's *acceptance* depend on the header rather than on its own bytes", so
a merge that drops a column would turn a valid file invalid rather than
turning a number into a visible error. §9.22 is not a counter-example — see
the twin case, `parse/predicate-computed-twin-of-missing-name-refused`.
