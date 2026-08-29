# Contributing

## Sign-off, not a CLA

Contributions are accepted under the Developer Certificate of Origin. Sign
commits with `git commit -s`. There is no CLA: this project wants independent
implementations more than it wants the option to relicense.

## The standing rule

**The conformance suite is not written by whoever writes the reference
implementation.**

This is not a style preference. During design, two separate claims — "11
namespaces, 0 unprotected" and "15 mutants, 15 killed" — were both produced by
the person who wrote the code being checked. An independent adversary then
found 7 silent-wrong cases and 14 surviving mutants. Three occurrences of one
failure mode: *a verification artifact authored by the implementer measures the
implementer's imagination.*

So: a pull request that changes `reference/` should not also add the case that
covers it. Open the case separately, ideally from someone else, and ideally
written from `SPEC.md` without reading the implementation.

## The mutation gate

`just mutants` deliberately breaks the reference implementation and requires
the suite to notice. A mutant that survives is a hole in the suite, not a bug
in the mutant — unless no input can distinguish it from the original, in which
case add it to `EQUIVALENT` with the reason.

New cases are welcome without new code. A case that fails is a bug report with
a reproduction attached.

## Before opening a PR

    just check && just test
