# Why this case exists

`signed = [ "-" *WSP ] literal` admits a minus and no plus, which matches
§4.1.6's `number` — `number = [ "-" ] 1*DIGIT [ "." 1*DIGIT ]` — and §4.1.6's
reason: a leading `+` is "a second spelling of a value that already has one, and
a second spelling compares equal as a number and unequal as text, which splits
`where` predicates and key identity from arithmetic."

`eval/number-leading-plus-refused` pins that for a cell. This one pins it for a
bound, which is a separate code path: `signed` was added after that case existed
and an implementation that implements it by handing the token to its host's
number parser gets `+1` for free, along with `1e3`, ` 1`, and every other
spelling §4.1.6 spent a paragraph refusing.
