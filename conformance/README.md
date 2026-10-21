<!-- SPDX-License-Identifier: MIT -->
# The conformance suite

The suite needs [kindkit](https://github.com/kindspec/kindkit). From a
checkout or an unpacked sdist, at its top level, either pip with the
`conformance` extra:

```sh
python -m venv .venv && . .venv/bin/activate
pip install '.[conformance]'
cd conformance
python run_cases.py                       # cases/
python run_cases.py --profile csv         # cases-csv/
```

or uv, whose `dev` dependency group pins the exact kindkit release CI runs:

```sh
uv sync                                   # the dev group is uv's default
cd conformance
uv run python run_cases.py                # cases/      (or: just conform)
uv run python run_cases.py --profile csv  # cases-csv/  (or: just conform-csv)
```

Each command runs one fixture tree; a full pass is both. A real `git` binary
is required. More in [Run it](../README.md#run-it).
