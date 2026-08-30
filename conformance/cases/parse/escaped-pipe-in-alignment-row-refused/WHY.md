# Why this case exists

§4.1.5: "Every cell of the second table line, trimmed, must match
`align-cell`", and `align-cell = [ ":" ] 1*"-" [ ":" ]`. The escape is a
cell-content rule (§4.1.3); it does not add a spelling to `align-cell`. The cell
`-\|-` unescapes to `-|-`, which is not one of the four spellings, so §9.20
refuses the file.
