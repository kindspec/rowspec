# Why this case exists

The rows are out of key order and the file meets no other refusal.

§10: "`canon` also puts the rows in key order, moving each row's line whole. §9.28 is the one refusal it repairs: a table that meets §9.28 and no other refusal canonicalises, and the result is valid."

Moving a line whole changes no cell, so `n` is 7. The file has no value as written, being refused by §9.28, so this case reads the values of the repaired file.
