`columns` is an empty object. `n` holds `1` and `abc`.

§13: "`columns` declares the type of any stored column, the key and order
columns included: a JSON object whose members map a column name to `number`,
`date` or `text`. Any other type, a non-string included, is refused, and so
is a `columns` that is not an object. Two members naming one column, such as
`café` spelt NFC and NFD, are refused as a repeated member is. Each trimmed
value of a named column is classified as an order value is, and refused when
its type is not the declared one: `text` means a value matching neither
`number` nor `date`, so `5` in a `text` column is refused, and `inf`, which
is text by §4.1.6, is refused in a `number` column and admitted in a `text`
one. A number beyond binary64 matches `number` and is admitted: it is
`#REF!(overflow)` where it is used (§8), and nothing here sorts by it."

An empty object maps no column to a type, so nothing is checked and the file
is accepted. A reader that refuses an empty `columns` refuses it.
