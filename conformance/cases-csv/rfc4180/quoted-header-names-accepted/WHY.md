Quotes around header fields are RFC 4180 syntax, so the column names are
`id` and `name`, not `"id"` (which `ident` would refuse). The sidecar's
`id` must find the quoted column.
