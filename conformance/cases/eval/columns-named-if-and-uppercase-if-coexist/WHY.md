# Why this case exists

This is §4.2 rule 4's own motivating example, made into a file. Rule 4, as
amended: "**Every function name in this document is matched case-sensitively**,
despite RFC 5234 §2.3 making a bare ABNF string literal case-insensitive. Read
the literals in this section as `%s`-prefixed. **[CHOICE]** ... a table may have
columns named both `IF` and `if`, and under case-insensitive function matching
rule 4 could no longer say which of them `IF(` refers to."

Three occurrences of the same three letters in one header cell, and each is a
different thing:

- `if(` — lower-case and immediately before `(` — is the function.
- `IF` — upper-case, in the comparison's left-hand `ident`, a name position by
  rule 7 — is the column holding `1` and `-1`.
- `if` — lower-case, in a branch, not before `(` — is the column holding `7`.

`s` is `7`: `r_01` takes the then branch and yields the `if` column's `7`,
`r_02` takes the else branch and yields `0`.

The file also asserts, silently, that `if` and `IF` are **not** a duplicate
column name under §9.2. §3 fixes NFC and says nothing about case folding, and
§4.1.9's allowlist admits both cases as distinct characters, so they are two
names. An implementation that case-folds identifiers refuses this file for a
duplicate that does not exist; one that case-folds *function* names cannot say
which column `IF(` would mean, which is the ambiguity rule 4's [CHOICE]
describes.

`parse/uppercase-if-is-an-unknown-function-refused` is the other half: `IF(`
before a paren is an unknown function (§9.11), not the conditional.
