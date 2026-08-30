# Why this pair exists

§9.23: "an `expr` nesting parentheses more than **64** deep (§4.2 rule 1)."

**The pair is the test.** A single refusal case pins only that *some* depth is
refused, and would keep passing if an implementation drew the line at 8, or at
4096, or wherever its call stack happened to give out. Two cases either side of
the number pin the number.

That the boundary must be *written down* rather than discovered is the finding
this replaces (see
`cases/eval/deeply-nested-parentheses-must-not-crash/RETIRED.md`): both
implementations used to raise `RecursionError`, which is neither of §9's two
defined outcomes, and each did so at a different depth because the limit was the
host language's call stack. §2: "An undocumented degree of freedom becomes an
interoperability bug the moment two implementations meet in one repository." Two
readers with different stack limits refuse different files, and neither reports
why.

64 is Excel's nesting limit, so the number is one the format's lineage already
carries. `rowspec_alt` has no limit and accepts both files.

This is the **refused** half: exactly 65, the first depth §9.23 excludes. It is
also the case that kills a mutant which raises or removes the limit, since a
larger limit still refuses 4096 but accepts this.
