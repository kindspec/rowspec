# Why this case exists

The first key is U+0065 U+0301 U+0062 and the second is U+00E9. Their NFC forms are U+00E9 U+0062 and U+00E9.

§6: "Where a key is declared, each data row's key MUST sort after the key of the row above it, compared as §4.1.8 orders text: by Unicode code point over the NFC-normalised, trimmed value. A table whose rows are not in that order is refused (§9.28)".

§9.28: "`rows-out-of-order`: a table that declares a key, and a row whose key does not sort after the key of the row above it, as §4.1.8 orders text (§6)."

After NFC the second key is a proper prefix of the first, so it does not sort after it. Compared on raw code points U+0065 is below U+00E9 and the table would pass.

Nothing else in the file is refused, so `rows-out-of-order` is the only identifier §9 allows. §3 compares identifiers after NFC and the two keys differ there, so §9.5 does not apply.
