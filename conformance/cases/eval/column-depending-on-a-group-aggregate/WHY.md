# Why this case exists

The group-aggregate twin of `eval/column-depending-on-a-row-relative-column`,
and the other half of what the second plain pass is for. `dbl` is an ordinary
formula whose operand is a group aggregate; §4.2 rule 9 requires it to have a
value, and it can only have one if ordinary formulas are evaluated again after
the group pass.
