# Why this case exists

§9.10: `order := by(c)` is refused where `c` "**is blank in any row**", and
§6: "Blank is none of `number`, `date` or `text`, so a column mixing blanks
with any of them mixes types."

The order column here is otherwise numeric — the common shape, a day number
— so this input is refused under either clause of §9.10: by the blank rule
directly, or by "mixes types" once the blank is typed by inference as text.
It therefore pins the verdict but not the blank rule specifically;
`parse/order-blank-cell-in-a-text-column-refused` is the input on which only
the blank rule fires, and the two belong together.

This is a `parse` case asserting refusal, deliberately: one implementation
historically *crashed* on this input rather than refusing it. The runner
reports an unexpected exception as a failure distinct from a `Malformed`
refusal, so an implementation that regresses from refusal to traceback fails
this case — recognition being total ("every byte sequence has exactly one
defined outcome", §9) is what is being pinned, not just the verdict.

`refusal_contains` is `""` because §9.10 mandates the refusal without
mandating a message.
