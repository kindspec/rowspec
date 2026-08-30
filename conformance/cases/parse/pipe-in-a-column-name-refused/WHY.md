# Why this case exists

The header twin of `parse/pipe-in-a-key-value-refused`, and the place where the
escape and the identifier allowlist collide most directly.

The header IS a table line, so §4.1.3 splits and unescapes it: `| id | a\|b |
qty |` declares a column whose name is `a|b`. §4.1.9's ABNF is
`ident = 1*( LETTER / MARK / NUM / "_" )`, which excludes `|`, and §9.16 refuses
"an identifier — column name, ... — containing ... any character outside
`ident`".

So `\|` is well-formed *as a cell* and the name it produces is ill-formed *as an
identifier*. Making a pipe writable in data did not make it nameable, and the
two rules meet on exactly one line of every file.
