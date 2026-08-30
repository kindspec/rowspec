# Why this case exists

SPEC.md §9.1 and §4.1.12 define a conflict line as "any line whose **first seven
characters** are seven `<`, seven `=`, seven `>`, or seven `|`". This line's
first character is `|`, so it is a table line whose second cell happens to hold
seven equals signs.

The case exists because §9.1 also says "anywhere in the file", and an
implementation that reads that as a substring search over the bytes -- rather
than the line classification §4.1.12 defines -- refuses a valid artifact. §4.1.5
draws the same distinction for alignment rows ("a single cell of `---` beside
ordinary values is data"), so this is the conflict-marker instance of a rule the
format already commits to.
