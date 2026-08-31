# Why this case exists

§4.1.10: "**The scan for that `#` skips string literals**, because §4.2 rule
6's `string` may contain both `WSP` and `#`. So `g := sum(a where r = "x #y")`
has no inline annotation and the predicate matches the value `x #y` ... an
implementation that follows the sentence truncates the line mid-string and
**refuses a valid file** — measured, on exactly this input."

This is an `eval` case, not a `parse` one, because acceptance alone is not
the rule: an implementation could accept the line and still mis-parse the
predicate. The rows are chosen so every wrong reading has a distinct sum —
matching `x` gives `7.0`, matching `x ` or truncating gives something other
than `16.0`, and only the literal `x #y` selects rows 1 and 3.

`h` pins the other half: a declaration whose string contains `#` may STILL
carry a real inline annotation after its `rhs`, so the scan must resume after
the closing quote rather than being disabled by it.
