# Why this case exists

#279, with one more backslash. The data row is `| r_1 | x\\|`: two
backslashes, then the line's last `|`.

SPEC.md §4.1: `table-line = *WSP "|" 1*( cell "|" ) *WSP eol`,
`cell = *( escaped / ( char - "|" ) )` and `escaped = "\" "|"`, with the
note that `cell` is ambiguous as written and that "The split is NORMATIVELY on
unescaped pipes: `escaped` wins." §4.1.3: "Both the leading and the closing `|`
are required. A cell may contain a pipe **only** as `\|`, and that is the
format's sole escape."

The `\` immediately before the `|` makes `\|`, which is `escaped`. The
first `\` is followed by `\`, not by `|`, and §4.1's note says "A
backslash not followed by "|" is a literal backslash." There is no escape
for the backslash: `\|` is "the format's sole escape", and §4.1.3 adds "No
other escape exists and none may be invented". So the line's last `|` is
escaped and the line has no closing `|`, as in
`parse/table-line-whose-last-pipe-is-escaped-refused`.

The defect this catches is a fix for #279 that borrows the convention of
most escaping languages and reads `\\` as an escaped backslash, which
leaves the `|` unescaped and the row accepted as `r_1` and `x\`. §4.1.3's
reason for forbidding an invented escape is this exact outcome: "an
unrecognised escape makes a file whose field count differs between
readers".

§9.18 `malformed-table-line`: "a table line that does not match `table-line`,
in particular one lacking its closing `|` (§4.1.3). **A line is a table line
for this purpose when its first non-`WSP` character is `|`** [...] Such a line
meets both entries, so under §9's note below either identifier is a correct
report". The other entry is §9.19 `unclassified-line`, since the line matches
no alternative of `line`. §9 also says "no conformance case asserts the
narrower one alone", so the case lists both, as
`parse/table-line-missing-closing-pipe` does.

No other entry applies, for the reasons given in the sibling case.
