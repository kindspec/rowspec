# Why this case exists

Two rules meeting. §4.1.4: "A cell's value is its text with leading and trailing
`WSP` removed, and nothing else removed". §4.2 rule 10: "A blank cell's text is
the empty string, so the equality is true."

The `q` cell of `r_01` holds three ASCII spaces. After §4.1.4 its value is the
empty string, so the blank test is true and `x` is `1`. An implementation that
tests the raw cell bytes — or that trims only for *some* purposes, which is the
common shape of this bug, since padding is usually stripped in the renderer
rather than in the reader — answers `0`.

§4.1.4 says why trimming must be in the reader: "Trimming is also what makes
text comparison total: a row keyed `r_01` and a row keyed `<tab>r_01` must be
one duplicate (§9.5), not two rows that render identically." The blank test is a
text comparison and inherits that.

Note the boundary this case does **not** cross. §4 and §4.1.4 trim ASCII space
and horizontal tab and "nothing else"; a cell holding U+00A0 is *not* blank, and
`eval/non-ascii-space-padding-refused` pins the reason — those characters arrive
as thousands separators, so trimming them turns `1 500` into `1500`.
