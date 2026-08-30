# Why this case exists

The other half of §4.2 rule 1's `==` / `!=` entry, against §4.2 rule 10's
`eq-op = "<>" / "="`.

`!=` is the more dangerous of the two. `==` at least fails loudly in a reader
that tokenises `=` maximally, because it sees `=` followed by `=` where an
`eq-rhs` belongs. `!=` starts with a character the grammar does not use
anywhere, so a reader that dispatches on the *second* character — or that
normalises `!=` to `<>` on the way in, which is what a spreadsheet-compatibility
layer does — accepts it silently and computes a table.
