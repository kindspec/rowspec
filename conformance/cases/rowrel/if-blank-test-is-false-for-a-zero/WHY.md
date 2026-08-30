# Why this case exists

§4.2 rule 10's blank test compares **text**: "A blank cell's text is the empty
string, so the equality is true." A cell holding `0` has the text `0`, which is
not the empty string, so the test is false.

The failure this catches is a host-language reflex rather than a misreading:
`if (!cell)` is false for `0`, for `""` and for a missing key in every language
the implementers of this format write in, and an implementation that reaches for
emptiness-as-falsiness instead of `text == ""` returns `1` here. `0` is also the
single most likely value to sit in a column being blank-tested — it is what the
guard in rule 10's own example is defending against.

The mirror of this is `rowrel/if-blank-test-sees-a-whitespace-only-cell-as-blank`:
a cell that looks non-empty in the bytes and *is* blank after §4.1.4's trim.
