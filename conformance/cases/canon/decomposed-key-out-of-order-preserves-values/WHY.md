# Why this case exists

The keys are U+0065 U+0301 U+0062 and U+00E9, out of key order under NFC.

§10: "`canon` also puts the rows in key order, moving each row's line whole. §9.28 is the one refusal it repairs: a table that meets §9.28 and no other refusal canonicalises, and the result is valid."

§4.1.8: compare "by Unicode code point over the NFC-normalised, trimmed value". A `canon` that sorts on raw code points would leave this file as it is, and the result would still be refused.
