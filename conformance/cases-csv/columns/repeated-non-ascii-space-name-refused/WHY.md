# Why this case exists

Both header names are a single U+3000 IDEOGRAPHIC SPACE.

§13: a leading or trailing non-ASCII space "is part of the name", so each
name is U+3000, and the two are equal, a duplicate (§9.2). Column names are
exempt from §4.1.9's allowlist, so the names themselves are not refused. No
sidecar is supplied and the field counts match.
