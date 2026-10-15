# Why this case exists

The sidecar declares `id` the key. The first key value is `r1` with a
leading U+2003 EM SPACE.

§13: "**the values of a declared key are refused when empty, or when they
hold whitespace or a `Cf` format character** (§4.1.9, §9.16), after
trimming ASCII space and tab only (§4.1.4), so a leading or trailing
non-ASCII space is part of the value and is refused."
