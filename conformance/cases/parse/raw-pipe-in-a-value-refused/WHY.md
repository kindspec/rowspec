# Why this case exists

This is the half of the retired `parse/backslash-pipe-is-not-an-escape` that
survives the reversal. §4.1.3: "A cell may contain a pipe **only** as `\|`" —
so an unescaped pipe is still a delimiter, and this row has four fields against
a three-field header. §9.6 refuses it.

The reversal made `\|` writable; it did not make a bare `|` mean anything new.
Without this case the suite would say nothing about the unescaped form, and an
implementation could "fix" the dogfood corpus by treating any pipe as data —
which changes the field count of every row that has one.
