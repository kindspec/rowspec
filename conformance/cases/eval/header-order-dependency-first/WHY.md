# Why this pair exists

§4.2 rule 9: "**The order of columns in the header is not an input to any
value**", and it gives this exact pair as the worked example: "Under
[left-to-right evaluation], `| net = qty * unit | gross = net * 1.2 |` is a pair
of numbers while the same two columns written in the other order gives `gross`
as `#REF!(net)` — so the header's column order becomes a coordinate, and moving
a column, which §10's canonical form otherwise treats as a pure rearrangement,
changes a total."

The two fixtures hold identical data with the computed columns declared in
opposite order and assert identical aggregates. Neither case alone tests
anything; the pair is the test, and it is why they carry the same expectations
rather than being folded into one file.
