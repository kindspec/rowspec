# Why this case exists, and the two ways it can legitimately be closed

§8: "The evaluator is total, terminating, deterministic and free of
input/output." §9: "Recognition is total: every byte sequence has exactly one
defined outcome, and a parse error is *reported* separately from being
*handled*."

A `RecursionError` traceback is neither outcome. **Both implementations crash**
on this file — 250 nested parentheses, which `primary`'s recursion generates
without limit. The reference is fine at 230 and crashes at 250, so the boundary
is an artifact of the host language's stack, which is exactly the kind of thing
§2 says must not be observable: "An undocumented degree of freedom becomes an
interoperability bug the moment two implementations meet in one repository."
Two readers with different stack limits refuse different files.

This case asserts the ABNF's answer, 6.0, because `primary` is recursive with no
depth bound anywhere in §4.2. The other legitimate resolution is a **§9 entry
for a nesting limit** with a number in it — at which point this case flips to
`accept: false` and should be retired with a note. What is not legitimate is the
present behaviour, where the limit exists, is undocumented, and differs between
implementations by accident.

The depth is deliberately modest. No human writes 250 nested parentheses, but
nothing stops a generator, a merge, or a hostile commit from producing one, and
§8's totality is described in the same breath as a security property.
