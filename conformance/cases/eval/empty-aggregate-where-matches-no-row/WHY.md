# Why this case exists

§7's first route to the empty aggregate: a `where` predicate that matches no
row. `"ZZ"` appears nowhere in `region`, so every aggregate's operand multiset
is empty even though the table has data.

`sum` and `count` return their identity element `0`; `min`, `max` and `avg`
have none and are `#REF!(empty)`. Unlike the all-blank-column sibling, `n` is
`0` here: under a `where`, `count` counts matched rows, and none matched.

Note the predicate itself is fine — `region` exists. A predicate naming a
column that does not exist is `#REF!(name)` per §8, not `0`, and
`predicate-missing-column-is-ref-not-zero` pins that boundary; this case sits
just on the other side of it.
