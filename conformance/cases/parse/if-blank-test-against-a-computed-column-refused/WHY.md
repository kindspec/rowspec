# Why this group exists

§9.22, as amended: "an equality in a `where` predicate whose left-hand `ident`,
or whose `ident` after `@`, names a **computed** column (§4.2 rule 5) — and, for
the same reason, an `=`/`<>` comparison inside `if` whose right-hand side is a
`string` and whose left-hand `ident` names a computed column (§4.2 rule 10)."

§4.2 rule 10: "Rule 5's argument transfers word for word — §5 requires a
computed column's data cells empty, so the only available reading compares
against the *rendered* form of a number, and §2 leaves rendering to the
implementation. Measured on this document's own reference implementation,
`total` of `20` renders `20.0` and never matches `"20"`, so the comparison is
false in every row and says nothing; a reader that renders `20` matches every
row. Both report a number."

That is the whole hazard in one sentence: **two conforming readers, one file,
opposite answers, no diagnostic on either.** It is not a hypothetical — the
measurement is of the reference implementation, and the construct was live and
silently returning `0` in every row before the clause was written.

The refusal is semantic, not syntactic. §9.22 says so — "no grammar can tell a
stored column from a computed one" — so nothing in the parser catches this and
an implementation that added `if` purely as a grammar change has no place for
the check to live.

**The three refusals are separate cases because they are separate code paths:**
`=` and `<>` are different operators, and `= ""` is the blank test, which an
implementation is likely to have special-cased *before* it reaches whatever
performs the §9.22 lookup. `parse/if-string-equality-against-a-stored-column-accepted`
and `eval/if-comparison-lhs-may-name-a-computed-column` are the two accepting
halves — the check must fire on *computed left-hand side and `string`
right-hand side*, and on neither condition alone.

**This one is the sharpest of the three**, and it is the case that made the
clause necessary rather than merely tidy. `""` is a `string`, so §9.22 reaches
it; and §5 requires a computed column's data cells empty, so a naive reading
would make `computed = ""` **true in every row** — a blank test that always
fires, over a column that is never blank in the sense rule 10 means. The
opposite reading, which the reference implementation had, compares against a
rendered `20.0` and is false in every row. A comparison that can only ever be
all-true or all-false, with the choice made by the implementation's number
formatter, is precisely the "says nothing" §9.22 now refuses.

The hazard is the special case. `if(x = "", a, b)` is the blank test, it is
named in rule 10 as such, and an implementation will recognise that token
sequence early — before it knows or cares whether `x` is computed. Routing
around the §9.22 lookup is not an oversight there; it is the natural
control flow.
