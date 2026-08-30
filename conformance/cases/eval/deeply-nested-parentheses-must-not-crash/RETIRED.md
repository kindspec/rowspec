# Retired, and why — the rule it tested was replaced, not relaxed

This case asserted that a formula with 250 nested parentheses **evaluates to
6.0**, on the strength of §4.2's `primary = literal / ident / "(" *WSP expr *WSP
")"` being recursive with no depth bound stated anywhere, and §8's "The
evaluator is total, terminating, deterministic".

It found a real defect: both implementations raised `RecursionError` — neither
of §9's two defined outcomes — and the boundary sat at a different depth in each,
because it was the host language's call stack rather than anything written down.

**The finding stood; the resolution went the other way, and correctly so.** The
case offered two closures and recommended neither strongly:

> This case asserts the ABNF's answer, 6.0 ... The other legitimate resolution
> is a **§9 entry for a nesting limit** with a number in it — at which point
> this case flips to `accept: false`. What is not legitimate is the present
> behaviour, where the limit exists, is undocumented, and differs between
> implementations by accident.

§9.23 now says 64, and the reasoning that picked it is better than the reasoning
in this case: making a parser survive 250 levels does not remove the
unspecified boundary, it moves it from the call stack to the heap and leaves it
equally unspecified. 64 is Excel's own nesting limit, so the number is one the
lineage already carries rather than one invented here.

Replaced by two cases, because a single refusal case pins only "deep is
refused" and not where the boundary is:

- `parse/nesting-depth-64-accepted`
- `parse/nesting-depth-65-refused`

The §2 argument this case was built on is preserved in both of them.
