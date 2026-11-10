# Why this case exists

`ours` moves `r_03` to the end and changes its `qty`. `theirs` deletes `r_03`.

§6: "Moving a line is a deletion and an insertion of the same line. With the move on one branch and a deletion of that row on the other, stock git removes the old line, keeps the new one, reports no conflict, and the deleted row comes back. No value or marker records that. Requiring key order refuses the moved row on the branch that moved it, and again after the merge, with nothing installed."

The moved line differs from the old one, but the merge still takes the deletion of the old line from both sides and the insertion from `ours`. The merged file has `r_03` last and is refused (§9.28).
