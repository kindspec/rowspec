# Why this case exists

The third header cell is `= 1`: its name, before the first `=`, is empty.

§4: "**Cell values are trimmed of leading and trailing ASCII space and
horizontal tab, and of nothing else.**" §4.1.4: "A cell's value is its
text with leading and trailing `WSP` removed, and nothing else removed",
with §4.1's "`WSP = SP / HTAB` — ASCII space U+0020 and horizontal tab
U+0009, never the Unicode `White_Space` property". §5: "**The split is at the cell's first `=`.**" So the name is the
empty string.

§4.1.9: column names "are `ident`: one or more Unicode letters, marks or
digits, or `_`", and `ident = 1*( LETTER / MARK / NUM / "_" )`. The empty
string is not an `ident`. §13 says as much by contrast: in the CSV profile
"column names are exempt from §4.1.9's allowlist … and so is an empty
header cell", which is an exemption only because the `.mdtbl` profile
refuses one.

§9.16 (`bad-identifier`) is the entry that refuses a column name outside
`ident` (§4.1.9). Only one column has the name, so §9.2 does not apply.
