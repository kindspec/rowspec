# Why this case exists

The companion to `parse/aggregate-call-inside-an-if-branch-refused`, with the
other kind of `call`. §4.2 rule 3: "A `call` never appears as a `primary`, and
`expr` has no call alternative — the two alternatives of `formula` do not
compose."

A branch of `cond` is an `expr`. `expr` reaches `primary`, and `primary` is
`literal / cond / ident / "(" expr ")"` — no `call`. So `cumulative(a)`
inside a branch is refused under §9.20, for exactly the reason
`cumulative(a) * 2` is.

`order := by(c)` is declared so the refusal cannot be mistaken for §9.9, "a
row-relative operator with no declared order". The file is refused for its
shape, not for a missing declaration, and an implementation that reports the
wrong one of those still passes — `refusal_contains` is `""` because §9's
numbering "is not a precedence order".

Rule 3's measured warning applies unchanged: handed a composition it does not
recognise, the failure mode is not a refusal but "leaves every `x` cell blank,
and reports `0` for `sum(x)`". Here that would be `s = 0` with a declared order
and a formula that reads as if it should run.
