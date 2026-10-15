# Why this case exists

The second and fourth header cells are empty.

§4: "**Cell values are trimmed of leading and trailing ASCII space and
horizontal tab, and of nothing else.**" §4.1.4: "A cell's value is its
text with leading and trailing `WSP` removed, and nothing else removed",
with §4.1's "`WSP = SP / HTAB` — ASCII space U+0020 and horizontal tab
U+0009, never the Unicode `White_Space` property". §5: "**The split is at the cell's first `=`.**" So both names are
the empty string, which is not an `ident` (§4.1.9: "one or more Unicode
letters, marks or digits, or `_`"); §9.16 (`bad-identifier`) applies.

The two names are also equal, so §9.2 (`duplicate-column`) applies. §9:
"where several apply, the case names each of them, and reporting any one
passes."
