`r2` holds order value `5` and sits last, the shape of a file in which an edit took `r2` from `2` to `5` and the line moved with it.

§13: "The rows MUST be in ascending order of the tuple `(typed value of the column, key)`, numbers by value, dates by year, month and day, text and the key as §4.1.8 orders text, or the file is refused (§9.28). A row may hold the same order value as the row above it, when its key sorts after that row's."

The rows ascend by the tuple, so the file is accepted, and rightly: in a CSV with `order`, a changed order value moves its line.

This is also what a merge leaves when that edit meets a deletion of `r2` on the other branch: §6's moved line, removed at its old place on both sides and kept at its new place. §13's rule has nothing to refuse, because the line now belongs where it is. The file does not record that the row was deleted, and no CSV-profile rule can see it.
