# Why this case exists

§4.2 rule 4: "**Every function name in this document is matched
case-sensitively**, despite RFC 5234 §2.3 making a bare ABNF string literal
case-insensitive. Read the literals in this section as `%s`-prefixed."

So `IF` before `(` is "a name before `(` that is in neither list", which rule 4
makes an unknown function — §9.11.

**This case was written before that sentence existed, and it is the reason the
sentence exists.** The document's ABNF was bare, RFC 5234 §2.3 makes `"if"`
match `IF`, `If` and `iF`, and nothing anywhere said otherwise — yet every
fixture in this tree and every implementation that lexes identifiers
case-sensitively refused it. The two readings differ on real data, because a
spreadsheet export writes `IF` in capitals by convention and that is the
spelling a migrating user's files arrive in.

Rule 4 now gives the reason as well as the rule: "a table may have columns named
both `IF` and `if`, and under case-insensitive function matching rule 4 could no
longer say which of them `IF(` refers to. One case convention, applied
everywhere, costs an importer one `lower()` and costs a reader nothing."

`eval/columns-named-if-and-uppercase-if-coexist` is that table, and it is the
other half of this case: here `IF(` is refused, there `IF` is an ordinary column
name sitting beside a column named `if`. Neither file makes sense without the
rule, and under the case-insensitive reading the second one has no defined
meaning at all.

The rule reaches all nine names, not just `if`. `SUM(` has the identical
question and this tree still has no case for it.
