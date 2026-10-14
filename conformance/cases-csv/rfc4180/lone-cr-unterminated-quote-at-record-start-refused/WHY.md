Records end in a lone CR, which CSV mode reads as a record break and
warns on (§13). The third record opens a quoted field at its start that
is never closed, so the file ends inside it and is refused (§13,
record boundaries). Issue #94 item 4.
