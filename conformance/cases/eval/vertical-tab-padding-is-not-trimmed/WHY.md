# Why this case exists

The second `q` cell is `5` with a U+000B VERTICAL TAB on each side, inside the ASCII
spaces that delimit the cell.

§4.1: "`char` is any scalar value other than `CR` or `LF`", and
`eol = LF / CRLF ; a lone CR is refused (§3)`. A line ends at LF or CRLF
and nowhere else. So the U+000B VERTICAL TAB is cell content, not a line break.

§4: "**Cell values are trimmed of leading and trailing ASCII space and
horizontal tab, and of nothing else.**" §4.1.4: "A cell's value is its
text with leading and trailing `WSP` removed, and nothing else removed",
with §4.1's "`WSP = SP / HTAB` — ASCII space U+0020 and horizontal tab
U+0009, never the Unicode `White_Space` property".

U+000B VERTICAL TAB is not `WSP`, so it stays in the value, which does not match
`number`. §4.1.6: "A cell is read as a number only if it matches `number`." §8:
"A value that will not coerce to a number is `#REF!`, not a guess:
thousands separators, parenthesised negatives, and non-ASCII spaces are
refused rather than interpreted."

`sum` coerces (§7), so `s` is `#REF!(q)`. A reader that trims with its host
language's whitespace class reads `5` and reports `6`.
