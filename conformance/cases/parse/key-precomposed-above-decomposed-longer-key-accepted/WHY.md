# Why this case exists

The first key is U+00E9. The second is U+0065 U+0301 U+0062, whose NFC form is U+00E9 U+0062.

§6: "Where a key is declared, each data row's key MUST sort after the key of the row above it, compared as §4.1.8 orders text: by Unicode code point over the NFC-normalised, trimmed value. A table whose rows are not in that order is refused (§9.28)".

After NFC the first key is a proper prefix of the second, so the rows are in order. Compared on raw code points U+00E9 is above U+0065 and the table would be refused. The twin `parse/key-decomposed-longer-key-above-precomposed-refused` holds the keys the other way up.
