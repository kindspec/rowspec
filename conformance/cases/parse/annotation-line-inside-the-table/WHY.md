# Why this case exists

SPEC.md §4: "The table is a contiguous run of lines beginning with `|`."
SPEC.md §9: the ignorable channel is "a line whose first non-space character is
`#`, **outside the table**".

A `#` line between two data rows is therefore not in the ignorable channel, and
it ends the table's contiguous run. What follows -- `| r_02 | gadget | 5 |` --
is then neither a blank line nor a declaration, so the file is refused. §4's
general rule settles the rest: "A reader that cannot recognise a construct MUST
refuse it, and MUST NOT degrade a failed recognition into a different
successful one."

`rowspec.table` ACCEPTS this file and evaluates both rows, silently extending
the table across a line that does not begin with `|`. `rowspec_alt.table`
refuses it. The two implementations disagree on how many rows this file has,
which is exactly the silent divergence the format exists to prevent.

I judge the reference at fault: the alternative reading requires §9's channel to
apply inside the table, and §9 says the opposite in the same sentence that
defines it.
