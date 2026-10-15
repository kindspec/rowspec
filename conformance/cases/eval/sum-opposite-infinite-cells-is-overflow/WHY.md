# Why this case exists

Column `a` holds 10^400 (a `1` and 400 zeros) and its negation. Both are
well-formed `number`s under §4.1.6, and both binary64 values are infinite,
one positive and one negative.

The tempting answer is `0`: the exact decimal sum of the two spellings is
zero, and §7 defines `sum` as "the correctly-rounded binary64 value of the
**exact mathematical sum** of the values it aggregates". But the values it
aggregates are the operands, and §8 settles what each operand is: "A
**stored** cell whose decimal spelling is finite but whose binary64 value is
already infinite is `#REF!(overflow)` wherever it is used as an operand."
§4.2 rule 2 says every operand "is converted to a binary64 double" first.
So both operands are `#REF!(overflow)`, and §8's "An aggregate poisoned by a
`#REF!` among its operands carries THAT error, unchanged" makes `sum` and
`avg` both `#REF!(overflow)`.

Two wrong outcomes this rules out besides `0`: a host summation of `+inf`
and `-inf` produces `NaN`, which §4.2 rule 2 says "cannot arise", or raises;
either way the evaluator is not total (§8: "total, terminating,
deterministic"). The answer is a value, and that value is
`#REF!(overflow)`.

`avg` is asserted beside `sum` because its exact mean is also zero and §7
defines it separately from `sum`.
