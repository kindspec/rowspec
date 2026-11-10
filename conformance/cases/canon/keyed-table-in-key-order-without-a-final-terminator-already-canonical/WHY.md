# Why this case exists

A keyed table in key order, in canonical form, whose file ends with no terminator after its last line.

§10: "The file's final terminator belongs to the file's last line, not to a row: if the file ended with no terminator it still does, after the rows have moved."

§4.1.1: the final terminator's presence or absence "is preserved by `render` and by `canon`, which never adds one".

Nothing here needs to change, so `canon` must return the file byte for byte, and a `canon` that adds a final `LF` fails.
