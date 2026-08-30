# Why this case exists

The mirror of `eval/predicate-literal-pipe-is-raw-in-a-declaration`. A header
cell **is** part of a table line, so §4.1.3 does split and unescape it: the
formula the evaluator sees is `sum(amt where region = "KS TV | Action")`, and
the literal must therefore be written escaped in the header and raw in a
declaration.

Two spellings of one string, decided by which line the formula sits on. Both
cases pass on the reference, so this is the behaviour the format has; it is not
written down.
