# Why this case exists

§4.1.3: "a writer escapes every literal `|` it emits."

This is the semantic form of the guarantee, and the one that matches how the
defect actually reaches a repository: a tool sets a cell to a value a human
typed, `render` writes it, and the file is committed. If the escape is dropped
the row gains a delimiter, and the next reader sees a four-field row against a
three-field header — or, in a table with one more column, a *valid* row with
every value shifted one place and a total that is plausible and wrong.

Asserting the aggregate after the round trip, rather than the bytes, is
deliberate: it is the assertion that fails for the right reason.
