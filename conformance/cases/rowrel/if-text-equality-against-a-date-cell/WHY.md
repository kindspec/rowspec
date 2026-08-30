# Why this case exists

The sibling of `rowrel/if-ordering-on-a-date-cell-is-a-broken-reference`, on the
same cell with the other operator.

§4.2 rule 10: a `string` right-hand side "compares text under rule 6's
treatment, unchanged — trimmed, unescaped, NFC". Text, not dates. So `x` is `1`
— the characters match — and `y` is `0`, because `2024-1-2` and `2024-01-02` are
different strings even though §4.1.7 makes them the same date, and §4.1.7 says
so directly: "Mixed spellings in *different rows* of one column are all dates".

The asserted cell is `y`, because `x` is `1` under either reading and measures
nothing. `y` is `0` under the text rule and `1` under a date-aware one, and a
date-aware `=` is exactly what an implementation gets by reusing §6's typed
comparison — the same reuse the ordering sibling catches, arriving through the
other operator.

This is also the case that shows why the two operators cannot share one code
path: the ordering sibling wants `#REF!(q)` on this cell and this one wants a
text comparison on it, from the same column, in the same file.
