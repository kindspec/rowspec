# Why this case exists

The lines ascend by key and `day` runs 3, 1, 2.

§6: "`order := by(c)` does not relax the rule: it declares the order a computation reads the rows in, never the order of the lines."

The lines are in key order, which is all the rule asks. `rowrel/order-by-reads-column-order-over-key-ordered-lines-*` pin the order in which these rows are read.
