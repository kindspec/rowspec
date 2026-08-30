# Why this case exists

`canon/if-formula-preserves-values` asserts that `canon` does not *change* this
file's values; it cannot assert what they are, since its check compares the file
against its own canonicalisation and would pass on two identical wrong answers.
This case pins the numbers on the same bytes.

Everything about the file is padded or non-canonical — `:--` and `---:` in the
alignment row, interior padding in the data cells, spaces around the `>` and the
commas inside the formula — and none of it may reach a value. §4.1.5: alignment
is decoration. §4.1.4: a cell is trimmed of `WSP` and nothing else. §4.2 rule 8:
whitespace between the tokens of an `expr` is permitted and never required.

`s = 5.0` also carries the laziness assertion through the padding, since `r_02`
has a `qty` of `0`.
