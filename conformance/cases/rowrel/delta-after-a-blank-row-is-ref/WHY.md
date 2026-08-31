# Why this case exists

§7: "If the row before this one has a blank `c`, then ... `delta(c)` here is
`#REF!(c)`, because a difference needs a number." The wrong answer is `2.0`
(`7 - 5`, reading past the blank to the value two rows back), which is a
plausible day-over-day change built on a stale operand. Note `delta` errors
on BOTH the blank row and the row after it, while `prior` errors on neither
— the two operators need separate assertions because the pinned bug was one
guard shared by all three.
