# Identifier ambiguities in the CSV profile

None remain under SPEC.md at `df99ea1`. Every refusing case in
`cases-csv/` carries `refusal`.

## Settled by the amendment at `df99ea1`

SPEC.md at `72f41cf` left the identifier open for two inputs, and their
cases asserted only `refusal_contains: ""`. The amendment settles both, and
each case now carries `refusal` and quotes the deciding sentences in its
`WHY.md`.

1. `markers/marker-line-in-a-two-column-file-refused`: `"conflict-marker"`.
   It was open whether a conflict line in a file of more than one column was
   also a record of one field, and so also §9.6. It is not:

   > §13: "A conflict line is classified first, and does not count as a row:
   > §4.1.12 classifies it "before any other classification"."

   > §13: "A record that starts on one does not count as a row (above), so it
   > is not also §9.6 `row-field-count`, and a file of nothing but conflict
   > lines is not also §9.13 `no-table`."

2. `order/order-type-with-order-naming-no-column-refused`:
   `"bad-order-column"`. It was open whether a valid `order_type` beside an
   `order` naming no column was also `malformed-declaration`, as "declares
   what cannot be checked". It is not:

   > §13: "This list is complete: a sidecar is `malformed-declaration` for
   > these reasons and no others, and the clause before the colon says why
   > they are, without adding to them."

   > §13: "`order_type` is judged only against an order column that exists,
   > so a valid `order_type` (one of `number`, `date` or `text`) beside an
   > `order` naming no column is none of these, and that sidecar is §9.10
   > `bad-order-column` alone. A `columns` member naming that same missing
   > column is still the last item."

   The `columns` question this file raised at `72f41cf` is settled by that
   last sentence, and `types/columns-member-naming-a-missing-order-column-refused`
   now pins it: `["bad-order-column", "malformed-declaration"]`.

## Considered and settled by the text

These inputs looked open, but SPEC.md decides the identifier, at `72f41cf`
and unchanged at `df99ea1`. Each case's `WHY.md` quotes the deciding
sentence.

- **A sidecar whose bytes are not UTF-8**
  (`sidecar/non-utf8-byte-in-a-name-refused`,
  `sidecar/utf16le-without-bom-non-ascii-name-refused`): `bad-encoding`
  alone, not also `malformed-declaration` for "not valid JSON". §9.14 is
  "decided before any line is classified". §13 gives the same bytes-first
  answer for a UTF-16 sidecar with a byte-order mark: "its bytes are not
  well-formed UTF-8, so it is `bad-encoding`".
- **An `order` that is not a string** (`order/not-a-string-refused`):
  `malformed-declaration` alone, not also `bad-order-column` for "an `order`
  naming no column". §13 lists `order` among the members "that is not a
  string", and keeps that case apart from naming no column: "A name that is
  not a string, or that names no column, is refused".
- **A refused `delimiter`** (`delimiter/*-refused`, except
  `semicolon-applies-refused`): `malformed-declaration` alone. With the
  delimiter refused there is no separator to split the CSV by, and under
  the default comma every fixture's rows are well formed.
- **An empty CSV whose sidecar declares a key**
  (`table/empty-file-with-a-key-sidecar-refused`): `no-table` and
  `malformed-declaration`. The file has no header row, so `key` names "no
  column of the file".
- **A refused file that also warns** (lone CR or leading BOM): the warning is
  not listed. §13: "A warning, §9.26's and §9.15's included, is not a
  refusal, and is not checked against the case's identifiers."
