# Why this case exists

§4.2 rule 10 gives `=` and `<>` one rule, not two: "`=` and `<>` compare **text
or numbers, and the right-hand side's spelling decides which**."

`<>` is written separately from `=` because it is the token an implementation is
most likely to leave out or to mis-lex. `comparison` tries `order-op` before
`eq-op`, and `order-op` contains `<`; a hand-written lexer that consumes `<` and
then looks for `=` finds `>` and either refuses the formula or reads it as two
operators. Under the text reading only `r_02` (`3.0`) differs from `"3"`, so the
total is `1`.

Its sibling `eval/if-not-equal-with-a-literal-rhs-compares-numbers` is `0` on
the same data, which is the discriminating pair.
