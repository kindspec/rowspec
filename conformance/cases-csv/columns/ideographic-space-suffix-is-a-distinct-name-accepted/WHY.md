# Why this case exists

The header is `id`, `a`, and `a` followed by U+3000 IDEOGRAPHIC SPACE.

§13: "A leading or trailing non-ASCII space, such as U+00A0, is part of the
name, as it is part of a key value, so `a` and `a<U+00A0>` are two names: a
look-alike of the kind the next sentence says is not refused." U+3000 is a
non-ASCII space, so `a` and `a<U+3000>` are two names and the file is
accepted.
