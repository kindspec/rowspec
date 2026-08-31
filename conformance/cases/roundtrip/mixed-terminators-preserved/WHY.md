# Why this case exists

§3 and §4.1.1: `LF` and `CRLF` both round-trip byte-exactly. Normalising
terminators to `LF` is `canon`'s job, and *only* canon's — a patch once
applied the normalisation to the wrong function, so `render` rewrote
terminators, and no case in the tree caught it in this shape.

`roundtrip/crlf` covers the uniformly-`CRLF`, alignment-padded file. This
input is different on purpose: canonical content with **mixed** terminators
(`LF` table lines, `CRLF` declarations) — exactly the file a
declarations-byte-verbatim canon used to emit, and exactly the shape on which
"normalise in the wrong function" shows.

It is **byte-identical** to the input of
`canon/crlf-declaration-terminator-normalised`. The pair forces the
amendment's split on the same bytes: `render(structure(x)) == x` here, while
`canon(x) != x` there.
