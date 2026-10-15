# Why this case exists

The twin of `parse/header-predicate-missing-name-before-a-computed-column-refused`,
with the last equality naming the stored column `a` instead of the computed
`b`. Every name the formula fails to resolve is a value by §8 ("A name in the
predicate that does not resolve is `#REF!(name)`, not a refusal", and §4.2
rule 7 for the aggregated column), and no equality names a computed column,
so §9.22 does not apply. The file is accepted.

The pair pins that the twin's refusal comes from `b`, not from the missing
names.
