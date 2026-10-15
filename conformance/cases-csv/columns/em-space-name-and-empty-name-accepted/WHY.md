# Why this case exists

The header is `id`, a single U+2003 EM SPACE, and an empty cell.

§13: "**A name is trimmed of ASCII space and tab only before §9.2 compares
it**, as a key value is (§4.1.4) … A leading or trailing non-ASCII space,
such as U+00A0, is part of the name".

U+2003 is a non-ASCII space, so it is not trimmed, and the name U+2003 and
the empty name are two names. No sidecar is supplied and the field counts
match, so nothing is refused.
