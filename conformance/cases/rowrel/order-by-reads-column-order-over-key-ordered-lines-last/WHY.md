# Why this case exists

The lines are in key order and `day` runs 3, 1, 2. So the derived order is `r_02`, `r_03`, `r_01`, and `cumulative(amt)` runs 1, 101, 111.

§6: "`order := by(c)` does not relax the rule: it declares the order a computation reads the rows in, never the order of the lines." §6: "A row's position in the file is never an input to any computation."

This case asserts row 2 of the derived order, which is 111.0. A reader that takes the lines as the order gets a different value.
