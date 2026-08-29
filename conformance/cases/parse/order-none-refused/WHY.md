# Why this case exists, and why it currently FAILS

SPEC.md §6 defines exactly two states for row order: `order := by(c)`, or the
line "omitted entirely". There is no `none()` form anywhere in the format.

§4: "A reader that cannot recognise a construct MUST refuse it, and MUST NOT
degrade a failed recognition into a different successful one."

`order := none()` is an unrecognised order construct. Degrading it into the
different successful outcome "this table declares no order" is the precise
move §4 forbids -- the same move that consumed a data row when an alignment
row was unrecognised. §9.12 ("a malformed declaration") is the refusal it lands
under.

The stakes are not cosmetic. §6: "Without `order`, the table is a SET and the
row-relative operators of §7 are refused." An author who writes `order :=
none()` and gets silence has been told their intent was understood. If they
later add `cumulative()`, they are refused for a reason that does not mention
the declaration they actually wrote.

## Resolution

When this case was written the reference ACCEPTED this file and evaluated it as
an unordered table -- a failed recognition degraded into a different successful
one. The implementation was corrected during the same pass and now refuses it:
"order must be by(<column>); omit the line entirely for an unordered table".

Its sibling `parse/order-unrecognised-construct-refused` is the same rule with
an argument (`order := none(day)`); that one the reference already refuses, and
it is what kills the `order-none-is-ignored` mutant.
