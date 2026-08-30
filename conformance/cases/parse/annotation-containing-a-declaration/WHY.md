# Why this case exists

SPEC.md §9: "Exactly one ignorable channel exists: **a line whose first
non-space character is `#`, outside the table**. It is preserved verbatim by
`render` and by `canon`, and it carries an *inertness promise*: nothing in it
may ever contribute to a computed value."

The definition is positional and total: FIRST non-space character is `#`. It
does not exempt lines whose remaining text happens to resemble a declaration.
An annotation that cannot contain the thing it is annotating is not an
ignorable channel -- and "# grand := sum(qty) times two" is the single most
likely thing a human writes in one: a note about the declaration below it, or
an old declaration commented out rather than deleted.

`rowspec.table` refuses any annotation line CONTAINING `:=`, whatever its first
character; `rowspec_alt.table`, written from the spec by an author who never
read the reference, accepts it. Two implementations, one artifact, opposite
outcomes -- accept versus refuse -- which is the §2 failure mode: "two
implementations that disagree here produce silent corruption rather than an
argument".

I judge the reference at fault. The spec is unambiguous and the second
implementation read it the same way I did.
