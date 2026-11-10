The sidecar declares `key` and no `order`: `r1` above `r2`.

§13: "Where the sidecar declares `key` and no `order`, the rows MUST be in ascending order of the key's value as §4.1.8 orders text, or the file is refused (§9.28)."

`r1` sorts before `r2`.

The twin `identity/key-only-out-of-code-point-order-refused` holds the keys the other way up and is refused.
