# Why this case exists

§7: `count` "is poisoned by a `#REF!` actually present in the column, because
that is an error value — but not by a value that merely fails to parse as a
number". The blank in `q` is the second kind — a blank is "exactly a value that
cannot serve as a numeric operand", and §7 says `count` counts blanks — but the
error is not in `q`, it is in `x`, where the ordering comparison put it.

So the two columns are treated differently on the same blank cell:
`count(q)` would be `2`, and `count(x)` is `#REF!(q)`, because `x` genuinely
contains an error value. An implementation that carries the carve-out one column
too far — skipping any cell it cannot read, wherever it came from — reports `2`
for `n` and `1` for `s`, both plausible.

§8 fixes the name the error carries through both hops: "the *originating* name —
the column that could not be resolved or whose value would not coerce, not the
column the error surfaces in", so it is `#REF!(q)` in `x`, in `n` and in `s`.
