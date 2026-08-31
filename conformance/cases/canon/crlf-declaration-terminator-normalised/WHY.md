# Why this case exists, and why it is filed under `removes-padding`

Amended §4.1.1: `canon` **normalises every terminator in the file to `LF`**;
"byte-verbatim" is about what an annotation or declaration *says*, not how it
ends. Before the amendment two implementations resolved the §3/§4.1.1
contradiction differently — one normalised everything, the other converted
table lines to `LF` and left declaration (and blank/annotation) terminators
byte-verbatim, emitting a canonical form with mixed terminators. Both were
idempotent, both passed every case in this tree, and their outputs were three
bytes apart. `canon/crlf-idempotent` asserts only idempotence and
`canon/crlf-preserves-values` only values; neither looks at bytes.

No `canon` check compares canon's output to expected bytes, and none of the
four can see this divergence directly:

- `idempotent` — both behaviours are idempotent.
- `preserves-values` — a terminator cannot reach a value.
- `already-canonical` — asserts `canon(x) == x`. Every fixed point of the
  correct canon (an all-`LF` canonical file) is also a fixed point of the
  mixed one, so no input separates them in the passing direction.
- `removes-padding` — its non-vacuity guard is the runner's **one assertion
  that `canon(x) != x`**: it fails when canon is the identity on an input
  containing a double space.

This case is built on that guard. The content is byte-for-byte canonical —
single-space cell padding, canonical alignment row, the annotation in the
position `canon/annotation-preserved` pins as a verbatim fixed point — and the
required double space sits *inside the annotation*, which is content canon
must preserve. The **only** non-canonical thing in the file is the `CRLF` on
the two declaration lines. A canon that normalises them changes the file and
passes; a canon that treats a declaration's terminator as part of its
"byte-verbatim" content is the identity here and fails with
"canon is the identity function on padded input".

The guard proves `canon(x) != x`, not the output bytes themselves; combined
with the content-verbatim and all-`LF` fixed-point cases already in the tree,
the only change canon can make to this file is the terminators.

Twin: `roundtrip/mixed-terminators-preserved` holds **byte-identical** input.
The pair forces the split the amendment states: `render` must return these
bytes unchanged, `canon` must not.

Sibling: `canon/crlf-annotation-terminator-normalised` pins the annotation's
own terminator the same way.
