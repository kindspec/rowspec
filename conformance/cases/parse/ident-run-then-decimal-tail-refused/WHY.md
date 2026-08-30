# Why this case exists

§4.2 rule 7, stated exactly: "A token is the longest run of `ident` characters
— except that where such a run is entirely ASCII digits and is immediately
followed by `.` and at least one ASCII digit, the token extends across the
`.`" — and the rule names this spelling as the refusal it implies: "`a1.5` is
the token `a1` followed by a character that no production admits", refused
under §9.20.

The run `a1` is not entirely ASCII digits, so the carve-out does not fire and
the `.` belongs to nothing. The table deliberately *has* a stored column named
`a1`, because the dangerous implementation is not the one that crashes — it is
the one that lexes `a1`, quietly drops the `.5`, and finds a perfectly good
column to resolve the remainder to. Against this file that implementation
accepts and computes `sum(out) = 7`; the case demands a refusal.
