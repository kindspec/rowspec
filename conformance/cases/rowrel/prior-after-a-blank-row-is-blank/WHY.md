# Why this case exists

§7: "**A blank in `c` is the preceding row's value, not a reason to look
further back.**" The wrong answer here is `5.0`, the value from two rows back
— precisely the "stale value, and a plausible one" the spec's own paragraph
names: "the reader sees a number that was true two rows ago and nothing says
so." An implementation that skips blank rows when walking backwards passes
`prior` on every input without consecutive data and fails only here.
