# Why this case exists

§8: "**An aggregate whose result is not finite is `#REF!(overflow)`** ... This
is stated separately because rule 2 scopes overflow to 'an **operation** whose
IEEE result is an infinity', and an aggregate is not an operation of `expr` — a
`sum` of a million large but finite cells overflows without any single
operation doing so."

Each cell is 9e307 written in plain digits — a finite binary64 value, well
inside range — and there is no computed column, so no operation of `expr` ever
runs. Only the aggregate's accumulation crosses into infinity. An
implementation that put its overflow check inside the `expr` evaluator — where
rule 2 told it to — and let `sum` accumulate raw doubles returns `inf` here:
a value §4.1.6 has no spelling for, which `canon` would write into a cell no
reader could read back. `eval/overflow-is-ref-overflow` already pins rule 2's
operation route; this is the aggregate route it does not reach.

Measured, not hypothetical: the reference returns `#REF!(overflow)`; on the
same bytes `rowspec_alt` dies with `OverflowError: intermediate overflow in
fsum` — a host accumulator's exception escaping uncaught, so the evaluator is
not total (§8: "The evaluator is total, terminating, deterministic") and the
answer is a traceback rather than either a value or a refusal. The case is
kept as written; the crash is the finding.
