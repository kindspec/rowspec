# Why this case exists

The mirror of `rowrel/if-unselected-branch-may-overflow`, on the same operands
with the branches swapped. There the overflow sits in the arm that is not taken
and must never happen; here it sits in the arm that *is* taken and must happen.

§4.2 rule 2: "**Overflow is `#REF!(overflow)`.** An operation whose IEEE result
is an infinity does not store one." §8, as amended: "**There are exactly four
`#REF!` shapes**, and an implementation emits no fifth ... `#REF!(overflow)` is
an operation whose IEEE result is an infinity (§4.2 rule 2)."

The pair is what distinguishes laziness from error-suppression. An
implementation that evaluates both branches and then discards the loser passes
this case and fails its mirror; one that catches and swallows overflow passes
the mirror and fails this one. Only *not performing the operation* passes both.

§8's paragraph is newly counted at four — it said *three* while rule 2 already
required `overflow` — which is worth a case rather than a footnote, because a
reader implementing from the old sentence had a documented licence to emit no
such shape and had to invent something. The available inventions are an
`inf`, which §4.1.6 cannot spell and §10 could not round-trip, and
`#REF!(big)`, which is §8's *name* shape and claims the column could not be
resolved when it resolved perfectly well.
