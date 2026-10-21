<!-- SPDX-License-Identifier: MIT -->
# The conformance suite

`run_cases.py` is the runner and `mutants.py` the mutation gate. Both drive the
fixture trees in `cases/` and `cases-csv/` through
[kindkit](https://github.com/kindspec/kindkit).

**The suite needs `uv sync` with the `dev` dependency group.** kindkit is in
that group, not in the package metadata, so `pip install` cannot provide it and
the runner fails with `ModuleNotFoundError: No module named 'kindkit'`. From a
checkout or an unpacked sdist, at its top level:

```sh
uv sync                                         # the dev group is uv's default
cd conformance && uv run python run_cases.py    # or: just conform
```

`uv sync` fetches kindkit from its pinned git commit, so it needs network
access and a `git` binary; the suite needs `git` anyway. Once kindkit is on
PyPI, a `conformance` extra can make `pip install` enough (#47).
