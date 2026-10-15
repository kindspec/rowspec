# Why this case exists

The header is a single space and a single horizontal tab.

§13: "**A name is trimmed of ASCII space and tab only before §9.2 compares
it** … so are a header cell of spaces, one of a tab and an empty one, so any
two of them are a duplicate." Both trim to the empty name, so the file is
refused (§9.2). No sidecar is supplied and the field counts match, so no
other refusal of §13's profile applies.

The CSV tree asserts only that a file is refused, never which refusal
(§13: "its conformance cases assert only that a file is refused"). This
case is built so that §9.2 is the only refusal SPEC.md gives it, but it
does not prove §9.2 is the one that fired: a reader that refused it for
another reason would pass too.
