# Why this case exists

The blank test doing the job rule 10 says it exists for: "without it there is no
way to write 'use this when that is missing'".

Two rules have to hold at once for `s` to be `6`. The blank test must be **true**
for `r_02` rather than `#REF!(q)` — otherwise `x` is an error there and §8
poisons `s`. And evaluation must be **lazy** — otherwise `q * 2` on the blank
runs anyway, and `eval/blank-in-arithmetic-is-ref` already pins that as
`#REF!(q)`, which poisons `s` just the same.

So the two headline behaviours of rule 10 fail this case identically, from
opposite directions, and both produce `#REF!(q)` rather than a wrong number. It
is included because it is the shape a user actually writes, and because it shows
the two rules are not independent: an implementation can only reach `6` by
having both.
