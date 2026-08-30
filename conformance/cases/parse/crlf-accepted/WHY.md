# Why this case exists

SPEC.md §3: "**Line endings are preserved.** LF and CRLF are both accepted and
round-trip byte-exactly; only the *canonical* form (§10) is LF."

"Accepted" is not "round-trips". The pre-existing `roundtrip/crlf` case only
exercises `render(structure(x))`, so nothing in the suite had ever asked a CRLF
file to PARSE or to EVALUATE. `rowspec_alt.table` refuses one outright --
"CRLF line endings; §3 requires LF" -- which is §3 as it read before the
CSV-corpus finding that 71 of 72 `iptv-org` files are CRLF. The suite let a
whole implementation sit on the retired rule undetected.

I judge the alternative implementation at fault, not the spec: §3 is now
unambiguous, and this case is the one that says so out loud.
