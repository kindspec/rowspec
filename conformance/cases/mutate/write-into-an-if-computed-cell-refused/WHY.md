# Why this case exists

§5: "A column with a formula is COMPUTED and its data cells are empty. Writing a
value into a computed cell is an error." §9.17: "a value in a computed cell".

`mutate/computed-col-refused` already pins this for an arithmetic formula. It is
worth pinning again for `if` because §9.17 is a property of *having a formula*,
and an implementation that recognises computed-ness by asking whether a header
cell parsed as an `expr` — rather than by asking whether it contains a `=` at
all — may classify a `cond` differently from `qty * unit`. That misclassification
is invisible until someone writes to the column, and then §5's invariant is
gone: the cell holds a value and the formula also produces one, and §10 has to
canonicalise a row that says two things.
