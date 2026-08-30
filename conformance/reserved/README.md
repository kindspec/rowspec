<!-- SPDX-License-Identifier: CC0-1.0 -->
# Reserved — cases for features not in this edition

These cases are **not run**. They test `lookup()`, the cross-artifact
reference, which is **reserved but not specified** in v0.

## Why they are kept rather than deleted

They were written by an adversarial case author and they encode design work
that would otherwise have to be redone. Between them they pin: resolution by
the target's declared key, an absent target row, a target with no declared key,
a column absent from the target, a missing target file, a self-lookup, a chain,
a cycle, a computed path, a path escaping the repository, and a target whose own
refusal must refuse the referrer.

Every one of those is a question `lookup` raises and the rest of the format does
not. That is why the feature was cut, and it is exactly why the cases are worth
keeping: **whoever specifies `lookup` inherits the question list already
answered in fixture form.**

## Why the feature was cut

`lookup` was, alone, the source of: input/output inside an evaluator §8
otherwise guarantees is pure; path confinement measured against a repository
root nothing defines; cross-artifact cycles; a target's refusal refusing the
referrer; a self-lookup reading the file on disk rather than the bytes under
evaluation; and the consequence that an artifact's validity is a function of
its bytes *and its lookup closure*, which §4.1 and §12 both otherwise deny.

Against that, only ~3% of real spreadsheet lookups translate mechanically to
it. It was paying the full complexity of a cross-artifact reference for a
fraction of its value, in the first edition of a format whose whole argument is
that a small representation beats a clever algorithm.

The syntax stays reserved so a later edition can define it without a migration.
