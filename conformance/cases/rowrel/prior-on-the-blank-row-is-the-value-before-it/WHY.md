# Why this case exists

§7: "If the row before this one has a blank `c`, then `prior(c)` here is
blank" — and, symmetrically, on the blank row itself `prior(amt)` is the
preceding row's value `5`, an ordinary number. `prior` is the one operator of
the three that does NOT error anywhere on this input: it reports the
preceding row's value, "blank included", and never coerces it. A single guard
written for all three operators — the bug this family pins — either errors
here too, or skips somewhere it must not.
