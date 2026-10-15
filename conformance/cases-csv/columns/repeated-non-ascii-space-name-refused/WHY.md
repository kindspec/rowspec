# Why this case exists

Both header names are a single U+3000 IDEOGRAPHIC SPACE.

§13: a leading or trailing non-ASCII space "is part of the name", so each
name is U+3000, and the two are equal, a duplicate (§9.2). Column names are
exempt from §4.1.9's allowlist, so the names themselves are not refused. No
sidecar is supplied and the field counts match, so no other refusal of
§13's profile applies.

The CSV tree asserts only that a file is refused, never which refusal
(§13: "its conformance cases assert only that a file is refused"). This
case is built so that §9.2 is the only refusal SPEC.md gives it, but it
does not prove §9.2 is the one that fired: a reader that refused it for
another reason would pass too.
