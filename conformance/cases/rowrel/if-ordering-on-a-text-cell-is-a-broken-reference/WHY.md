# Why this case exists

§4.2 rule 10: "an operand that is not a number — blank, text, or an error —
makes the whole `cond` that error, by §8, exactly as it would in arithmetic."

The blank case is spelled out in rule 10's own prose; text is only listed, and
it is the one an implementation is likelier to get wrong, because comparing a
string against a number is a *total* operation in several host languages —
Python 2 ordered them, JavaScript coerces and yields `false`, and a naive
`str(cell) > str(0)` compares `"abc"` against `"0"` and answers true. All three
produce a number here where the format produces an error.

§8 fixes the name: the error carries "the column that could not be resolved or
whose value would not coerce", so `#REF!(q)`.
