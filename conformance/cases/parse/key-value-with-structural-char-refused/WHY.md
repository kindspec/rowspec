# Why this case exists

SPEC.md §9.16: "an identifier -- column name, aggregate name, `key`/`order`
argument, or a value of the key column -- containing whitespace, a `Cf` format
character, or **any character outside `ident`** (§3, §4, §4.1.9)".

§4.1.9: "`ident` = one or more Unicode letters, marks or digits, `_`, `-`, `.`.
Whitespace and `Cf` are excluded by construction ... so are `|`, `=`, `:`, `#`,
`(`, `)`, `,`, `"` and `@`, each of which is structural somewhere -- a column
named `total (USD)` would be unquotable inside a formula, and `#` would be
indistinguishable from an annotation. [CHOICE] The set is an allowlist rather
than a denylist so that the answer for a character nobody has thought of yet is
*refused*, not *whatever this implementation's punctuation table happens to
say*."

**Both implementations accept this.** §4.1.9 is an allowlist on paper and
neither reader enforces it: of the nine structural characters the section
enumerates, the only one either refuses in any position is whitespace, and only
in the key column. The section argues for an allowlist precisely so that
unforeseen characters are refused; as implemented it is not even a denylist.

This fixture puts `@` in a **key column value**. §9.16 names "a value of the key
column" explicitly, and `@` is structural in §7's group-aggregate predicates
(`where region = @region`).
