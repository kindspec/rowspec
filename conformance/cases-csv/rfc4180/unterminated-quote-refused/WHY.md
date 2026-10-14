The quoted field opened on the second line is never closed, so RFC 4180's
grammar generates no record structure for the rest of the file. SPEC.md
names no CSV-specific refusal for this. Reading: §9 says recognition is
total and §4 says a construct the reader cannot recognise is refused, never
degraded; any lenient recovery invents a field count. Nothing else in the
file is a fault.
