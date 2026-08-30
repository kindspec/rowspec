# Why this case exists

The spelling rule of §4.2 rule 10 put on a second-spelling pair the format
explicitly **admits**. §4.1.6: "`007` and `1.50` satisfy it exactly and are
**admitted**, because refusing them would break zero-padded identifiers and
currency columns."

So `007` is the number seven and the text `007`, and the two comparisons in this
one header disagree about it: `code = 7` is numeric and true, `code = "7"` is
textual and false. Both columns are in the same file so an implementation cannot
pass by being consistently wrong.

This is the shape the rule costs something on. A reader who writes `= "7"`
against a zero-padded identifier column gets `0` and no diagnostic — which is
correct, and is exactly what §4.1.6 means by a second spelling that "compares
equal as a number and unequal as text".
