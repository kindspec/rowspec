The sidecar declares `key` and `order_type` `number`, and no `order`. `o`
holds two numbers.

§13: "**`order_type` without `order` is refused**, as `order` without `key`
is (§9.25): it declares a check with no column to run on, and ignoring it
would leave the author believing the check ran."

This tree asserts only that the file is refused (`refusal_contains: ""`),
because the CSV profile carries no §9 identifiers yet (§13). The case is
built so that `order_type` without `order` is the only fault in the file and
its sidecar, so a reader that refuses it has refused for that reason or for
one §13 does not give. What the case does not pin is which reason the reader
reports.
