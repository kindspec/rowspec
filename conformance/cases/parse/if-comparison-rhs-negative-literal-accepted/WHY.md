# Why this case exists, and what it used to say

`order-rhs = signed / ident` and `signed = [ "-" *WSP ] literal`, so a
comparison's bound may be negative and `if(a > -1, 1, 0)` is well-formed.

**This case was written as a refusal and is now an acceptance, and the history
is the reason it is worth keeping.** Before `signed` existed the grammar read
`order-rhs = literal / ident` with `literal` annotated *unsigned*, which made
`a > -1` — an entirely ordinary guard — unwritable, with no workaround short of
a stored column holding `-1`. Nothing in rule 10's prose mentioned the
restriction, so an implementation reaching `order-rhs` through its general
number lexer would have accepted `-1` without anyone deciding to, and one
reading the ABNF would have refused it. The refusal case existed to force that
choice to be made rather than inherited from a lexer.

It was made, and `signed` is the answer. The case flips rather than retiring,
because the boundary it guards did not disappear — it moved. `signed` wraps
`literal` and nothing else, so the three neighbouring spellings are still
refused, and each has its own case:

- `parse/if-comparison-rhs-negated-ident-refused` — `if(a > -b, …)`
- `parse/if-comparison-rhs-double-negative-refused` — `if(a > --1, …)`
- `parse/if-comparison-rhs-leading-plus-refused` — `if(a > +1, …)`

The semantics are `rowrel`/`eval` cases, not this one: an accept case cannot
tell an implementation that parses `-1` from one that parses it and then drops
the sign. `eval/if-ordering-against-a-negative-bound` is that test.
