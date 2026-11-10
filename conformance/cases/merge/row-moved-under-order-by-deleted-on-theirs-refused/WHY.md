# Why this case exists

The table declares `order := by(day)`. `ours` moves `r_03` to the end without changing its `day`, and `theirs` deletes it.

§6: "`order := by(c)` does not relax the rule".

§6: "Moving a line is a deletion and an insertion of the same line. With the move on one branch and a deletion of that row on the other, stock git removes the old line, keeps the new one, reports no conflict, and the deleted row comes back. No value or marker records that. Requiring key order refuses the moved row on the branch that moved it, and again after the merge, with nothing installed."

The merged file has `r_03` last, out of key order, and is refused (§9.28).
