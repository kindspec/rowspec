# rowspec_alt — the conformance witness

A second, independent implementation of the specification. It exists so the
conformance suite always has a consumer that is not the reference
implementation.

It was written by an author working from `SPEC.md` and `conformance/cases/`
alone, forbidden to read `reference/rowspec/`. That experiment is the reason
several sections of the specification say what they now say: the author passed
57 of 57 cases as the tree then stood, and then failed 9 of the 74 cases added
afterwards — every failure a documented guess that a fixture overturned.

Its verdict on the prose at that time was *"passing the suite is not evidence
the prose is sufficient; it is evidence the suite is small."*

Keep it independent. Do not "fix" it by copying from `reference/rowspec/`; when
the two disagree, that disagreement is information about the specification, and
resolving it by making the code identical destroys the only signal this
directory produces.
