# Retired, and why — do not restore this case without reading the measurement

This case asserted that `\|` is not an escape, citing SPEC §4.1.3 as it then
read: a cell can never contain `|` "because no escape exists and none may be
invented."

The case was right about the prose. **The prose was wrong, and a dogfood run
falsified it.**

Replaying 7,446 real commits from four public CSV-in-git repositories:

    refusal rate on real commits    26.95%   against a pre-registered 2% ceiling
    of those refusals, involving a `|` inside a value      95%
    admitted false positives                            1,863

The specific data: `KS TV | Action`. Ninety-three Ukrainian television channels
have a pipe in their own name. From 2023-10-16 to HEAD, **100% of that file's
commits were unrepresentable.** Before that date the same corpus refuses 1.6%
and passes the threshold comfortably.

The no-escape rule was written as a virtue — an escape is parser complexity
nobody needs — and it was never paid for by evidence. The first contact with
real data produced evidence against it. GFM has had `\|` for years, for exactly
this reason.

§4.1.3 now defines `\|` as the escape. This case is retired because the rule it
tested no longer exists, not because it was inconvenient to pass. Its inverse
now lives in `parse/backslash-pipe-is-an-escape`.
