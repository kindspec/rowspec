# Why this case exists

SPEC §7: "`count` counts rows and never coerces ... Without this, `count` can
never count a text column, which is surprising for a counting function and
follows from nothing anyone intended."

This is that sentence's positive form, and nothing in the suite asserted it
before: every other `count` fixture in the tree counts a numeric column, where
the row count and the coercing count agree. Nothing was wrong with this file,
and under the previous behaviour `count(name)` returned `#REF!(name)`.
