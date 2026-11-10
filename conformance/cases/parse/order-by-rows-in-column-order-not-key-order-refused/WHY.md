# Why this case exists

`day` ascends down the lines and the keys run `r_02`, `r_03`, `r_01`.

§6: "`order := by(c)` does not relax the rule: it declares the order a computation reads the rows in, never the order of the lines."

§9.28: "`rows-out-of-order`: a table that declares a key, and a row whose key does not sort after the key of the row above it, as §4.1.8 orders text (§6)."

Nothing else in the file is refused, so `rows-out-of-order` is the only identifier §9 allows.
