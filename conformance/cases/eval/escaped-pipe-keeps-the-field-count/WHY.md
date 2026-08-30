# Why this case exists

SPEC.md §4.1.3, as amended: "A cell may contain a pipe **only** as `\|`, and
that is the format's sole escape. A reader splits a table line on unescaped
pipes and unescapes `\|` in each cell; a writer escapes every literal `|` it
emits."

The value is `KS TV | Action` — the real datum from the dogfood run, where
ninety-three television channels in one public registry have a pipe in their own
name and every commit to that file was unrepresentable under the previous rule.

`rowspec_alt` has not been updated for the escape and refuses these files with a
field-count error; per the coordinator that is expected and is not a signal
about the specification.
