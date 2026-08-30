# Why this case exists

§4.2 rule 10: "`| x = if |` is a reference to a column named `if`". There is no
such column in this file, so §8's ordinary rule applies: "A reference to a name
that does not exist evaluates to `#REF!(name)`."

The value is the assertion. `parse` cannot reach this: the file is well-formed
under either reading, and the two wrong outcomes are a *refusal* — from a reader
that treats `if` as a keyword and finds no `(` after it — and a **blank column**,
from a reader that fails to recognise the cell and falls back to treating it as
a plain name. §4.2's "Recognition is whole-cell" paragraph names that second one
as the specific hazard: "the successful reading available to a lazy
implementation is 'treat the cell as a plain column name', which turns a broken
formula into a stored column of blanks."

Here the correct answer *is* a plain column name, and it is still an error,
because the column is absent. `#REF!(if)` is the only spelling that reports
both facts.
