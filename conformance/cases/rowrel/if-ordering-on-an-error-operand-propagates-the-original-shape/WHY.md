# Why this case exists

§4.2 rule 10: "an operand that is not a number — blank, text, or **an error** —
makes the whole `cond` that error, by §8, exactly as it would in arithmetic."

The word doing the work is *that*: the `cond` becomes **that** error, not a new
one. §8 fixes the same thing from the other end — "All three are values, all
three propagate identically" and "`#REF!(name)` carries the *originating* name
... not the column the error surfaces in."

So `x` is `#REF!(/0)`, the shape `e` already had, and **not** `#REF!(e)`. The
wrong answer is very available: a comparison that asks "is this operand a
number?" and, on being told no, reports a broken reference to the column it was
reading, produces `#REF!(e)` — which §8 calls a name shape and reserves for a
column that could not be resolved, and which a reader cannot distinguish from a
missing column actually named `e`. §8: "There are exactly three `#REF!` shapes,
and an implementation emits no fourth", and getting the shape wrong is emitting
the wrong one of the three.
