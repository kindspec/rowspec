<!-- SPDX-License-Identifier: MIT -->
# The conformance suite

The suite needs `uv sync` with the `dev` dependency group, which is where
kindkit is; `pip install` cannot provide it. From a checkout or an unpacked
sdist, at its top level:

```sh
uv sync                                   # the dev group is uv's default
cd conformance
uv run python run_cases.py                # cases/      (or: just conform)
uv run python run_cases.py --profile csv  # cases-csv/  (or: just conform-csv)
```

Each command runs one fixture tree; a full pass is both. Why kindkit is a dev
dependency, and when that changes: [Run it](../README.md#run-it).
