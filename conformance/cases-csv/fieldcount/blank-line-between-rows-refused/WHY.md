An empty line inside the data. Under RFC 4180's grammar it is a record of
one empty field (a reader that yields zero fields gets a mismatch too), and
the header has two, so §9.6 applies. Reading: CSV has no blank-line
channel; .mdtbl's blank line exists only outside the table (§4.1.2), and
skipping it silently would make the record count depend on the reader.
