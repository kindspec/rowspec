# Why this case exists

One half of a pair with `eval/sum-huge-cancellation-positives-first`: the same
multiset of four cells — `1e308`, `-1e308`, `1e308`, `-1e308`, each a finite
binary64, exact sum `0` — in the file order where a left-to-right binary64
accumulator happens to survive. This ordering is the control: nearly any
implementation answers `0` here. The sibling case holds the answer fixed while
only the file order changes, which is the whole content of §7's rule that an
aggregate is defined on the multiset of its operands and never on an
accumulation order.
