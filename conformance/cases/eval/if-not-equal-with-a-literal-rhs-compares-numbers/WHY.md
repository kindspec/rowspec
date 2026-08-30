# Why this case exists

The numeric half of `<>`, on the same data as
`eval/if-not-equal-with-a-string-rhs-compares-text`. §4.2 rule 10: "A `literal`
right-hand side compares numbers." Both cells are the number `3`, so neither is
`<> 3` and the total is `0`.

`0` is the assertion that makes the pair sharp: an implementation that reads
`<>` textually returns `1` here, which is a plausible number, and returns `0` on
the text file where the answer is `1`. Both files are needed and neither is
redundant.
