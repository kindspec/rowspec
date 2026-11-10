The keys are `a` and `b`, with more leading space before `b`.

§13: "Where the sidecar declares `key` and no `order`, the rows MUST be in ascending order of the key's value as §4.1.8 orders text, or the file is refused (§9.28)."

§4.1.8 compares the trimmed value. Compared with the padding left on, the extra space before `b` sorts first and the file would be refused.
