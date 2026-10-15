# Why this case exists

The header is a single space and a single horizontal tab.

§13: "**A name is trimmed of ASCII space and tab only before §9.2 compares
it** … so are a header cell of spaces, one of a tab and an empty one, so any
two of them are a duplicate." Both trim to the empty name, so the file is
refused (§9.2). No sidecar is supplied and the field counts match.
