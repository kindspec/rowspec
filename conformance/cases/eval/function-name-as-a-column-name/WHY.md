# Why this case exists

§4.2 rule 4: "**The function names are not reserved words.** The eight names of
`rowrel-fn` and `agg-fn` are recognised **only** immediately before `(`, with no
`WSP` between the two. So `| x = sum |` is a reference to a column named `sum`,
`sum` is a legal column name."

The reason: "reserving eight ordinary nouns would refuse a table with a column
named `count` or `min`, which is an ordinary table."

The declaration `s := sum(x)` in the same file uses `sum` as a function, so one
fixture holds both readings of the same six letters.
