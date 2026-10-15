The sidecar's `delimiter` is U+FEFF. The CSV starts with U+FEFF and uses it
between fields: `<FEFF>id<FEFF>name`, then `r1<FEFF>a` and `r2<FEFF>b`.

§13: "A file that starts with U+FEFF is read as starting with a BOM, warned
on as above, before its records are split, so this holds even when the
delimiter is U+FEFF: that first U+FEFF is never a separator."

§13 makes refusal 26 (`leading-bom`) a warning in CSV mode. The first U+FEFF
is a BOM, so the header is `id`, `name`, two fields, as is each row: the
file is accepted with a warning. A reader that splits before looking for a
BOM reads the header as an empty name, `id` and `name`, three fields against
rows of two, and refuses it.
