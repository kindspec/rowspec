# Why this case exists

§4.2 rule 9: "`| x = y | y = x |` and `| b = b + a |` are **accepted files**, not
refusals — the fixture tree requires it, and the reason it should is that a
cycle is a property of the whole header rather than of any one cell, so refusing
would mean one author's new column can invalidate another author's line, in a
merge where both lines are individually fine."

Nothing in rule 10 changes that, and the cycle arriving through an `if` branch
is the case where an implementation is most tempted to refuse: it has just been
told to run a static pass over both branches, and raising from that pass is
easier than threading a value out of it. §9's list is complete and contains no
entry for a cyclic header.

The value is pinned separately by
`rowrel/if-cycle-is-static-in-a-row-that-avoids-it`; this case pins only that
the file is a file.
