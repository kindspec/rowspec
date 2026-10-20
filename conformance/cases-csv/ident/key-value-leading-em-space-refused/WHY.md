# Why this case exists

The sidecar declares `id` the key. The first key value is `r1` with a
leading U+2003 EM SPACE.

§13: "**the values of a declared key are refused when empty, or when they
hold whitespace or a `Cf` format character** (§4.1.9, §9.16), after
trimming ASCII space and tab only (§4.1.4), so a leading or trailing
non-ASCII space is part of the value and is refused."

## Identifier

This case asserts `refusal: "bad-identifier"`.

§13: "Every CSV-mode refusal is reported with a §9 identifier, under §9's rules for reporting one. Each refusal this profile makes is read as a §9 entry, as follows, and is reported with that entry's identifier:"

§13: "a `Cf` format character in a column name, and a declared key's value that is empty or holds whitespace or a `Cf` format character: §9.16 `bad-identifier`."

§9.16: "`bad-identifier`: an identifier — column name, aggregate name, `key`/`order` argument, or a value of the key column — that is empty, or that contains whitespace, a `Cf` format character, or any character outside `ident` (§3, §4, §4.1.9)"
