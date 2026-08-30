# Why this case exists

§4.2 rule 8: "`WSP` — ASCII space and horizontal tab, §4.1's definition — is
permitted between any two tokens of an `expr` and is never required there".

A horizontal tab inside a formula is whitespace, not a value and not a refusal.
This is the one place a tab is *not* trimmed away before the grammar sees it:
§4.1.4 trims leading and trailing `WSP` from a cell, and this tab is interior.
