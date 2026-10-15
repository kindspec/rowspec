# Why this case exists

The first data line ends with a U+000C FORM FEED after its closing `|`.

§4.1: `table-line = *WSP "|" 1*( cell "|" ) *WSP eol`, and `WSP` is "ASCII
space U+0020 and horizontal tab U+0009, never the Unicode `White_Space`
property". A form feed is a `char`, not `WSP` and not `eol`, so the line
does not match `table-line`.

§9.18 (`malformed-table-line`): "A line is a table line for this purpose
when its first non-`WSP` character is `|`" and "Such a line meets both
entries, so under §9's note below either identifier is a correct report",
the other being §9.19 (`unclassified-line`). Both are listed.
