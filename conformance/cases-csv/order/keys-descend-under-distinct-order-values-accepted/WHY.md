`o` ascends and the keys descend.

§13: "The rows MUST be in ascending order of the tuple `(typed value of the column, key)`, numbers by value, dates by year, month and day, text and the key as §4.1.8 orders text, or the file is refused (§9.28). A row may hold the same order value as the row above it, when its key sorts after that row's."

The key is the second member of the tuple, so it decides only a tie, and these rows hold no tie. With `order` declared, §13 does not also require key order, which is the difference from §6's `.mdtbl` rule.
