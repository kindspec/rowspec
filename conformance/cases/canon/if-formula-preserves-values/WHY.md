# Why this case exists

§10: "Padded input is valid and round-trips byte-exactly; it is simply not
canonical, and canonicalisation is a separate explicit operation". The check is
that `canon` is value-preserving on a table whose computed column is an `if`.

The file is padded in every way §10 mentions and one it does not: the alignment
row uses `:--` and `---:` spellings, the data cells carry interior padding, and
the formula itself is written with spaces around its commas and its `>`. The
values on both sides must be `s = 5.0` and `n = 2`, which also means the
`r_02` guard must still fire after canonicalisation — a canonicaliser that
mangles the formula into something that parses differently, or into something
that no longer parses at all, changes `s` from `5` to `#REF!(/0)` or to nothing.
