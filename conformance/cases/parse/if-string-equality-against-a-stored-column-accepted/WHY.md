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

**This is the half that stops the fix from being worse than the bug.** The
table has a computed column (`total`) and a string comparison (`region = "EU"`)
in the same header, and the comparison's left-hand side is *stored*, so it is
well-formed.

§4.2 rule 10 issues exactly this warning about the neighbouring refusal:
"over-applying §9.22 to every `ident` in every comparison — one line, and it
looks like defence in depth — refuses it." The over-broad check has two shapes
and this file catches both: refusing any string comparison in a table that
happens to contain a computed column, and refusing any string comparison
whatever.
