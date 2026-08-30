# Why this case exists

§4.2 rule 8: "`#` is not whitespace and is not a comment inside a formula.
§4.1.10 is categorical that `#` inside a table line is data, so
`| x = a * 2 #note |` has a formula of `a * 2 #note`, which `formula` does not
generate, and the header cell is refused under §9.20. **An implementation that
borrows a host language's parser will silently read `#note` as a comment and
accept the file; that is the mechanism, and it is why this sentence exists.**"

Both implementations refuse it today. The case exists because the defect it
guards against is reintroduced by an ordinary refactor — swapping a
hand-written expression parser for the host language's — and nothing else in
the tree would notice.
