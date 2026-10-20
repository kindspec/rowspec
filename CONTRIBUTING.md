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

So: conformance cases are written by an author who has seen no
implementation, from `SPEC.md`, and they run against the implementation
unchanged. A case is never edited to make the code pass. The cases may land
in the same pull request as the code they check when that is where they
first run; give them their own commit, so they can be read as written.

#253 is an instance. The CSV profile's identifier cases were written from
`SPEC.md` by an author who had seen no implementation, and land in their own
commit. Their first run against the code caught one defect: a header of
blank cells was refused as `no-table` rather than `duplicate-column`, fixed in
`1d3626b`. After that fix the cases ran 280 of 280, unchanged.

## The mutation gate

`just mutants` deliberately breaks the reference implementation and requires
the suite to notice. A mutant that survives is a hole in the suite, not a bug
in the mutant — unless no input can distinguish it from the original, in which
case add it to `EQUIVALENT` with the reason.

New cases are welcome without new code. A case that fails is a bug report with
a reproduction attached.

## Before opening a PR

    just check && just test
