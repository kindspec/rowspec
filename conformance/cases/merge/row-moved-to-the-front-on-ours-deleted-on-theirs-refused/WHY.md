# Why this case exists

`ours` moves `r_03` to the front of the table. `theirs` deletes `r_03`.

§6: "Moving a line is a deletion and an insertion of the same line. With the move on one branch and a deletion of that row on the other, stock git removes the old line, keeps the new one, reports no conflict, and the deleted row comes back. No value or marker records that. Requiring key order refuses the moved row on the branch that moved it, and again after the merge, with nothing installed."

Both sides delete the old line, so git keeps the inserted one and reports no conflict. The merged file holds `r_03` first, which is out of key order, so the reader refuses it (§9.28) and the row cannot return unnoticed.

`ours` is itself a refused file for the same reason. The `merge` kind asserts only on the merged result, and `parse/row-moved-to-the-end-refused` and `parse/row-moved-to-the-front-refused` pin that shape on its own.
