# rowspec task runner

set dotenv-load := false

# Default: show available recipes
default:
    @just --list

# Install dependencies and set up environment
setup:
    uv sync

# Format code (mutates working tree — use locally)
fmt:
    uv run ruff format .

# Verify formatting (non-mutating — use in CI)
fmt-check:
    uv run ruff format --check .

# Run linters
lint:
    uv run ruff check .

# Format + lint (non-mutating — safe for CI)
check: fmt-check lint

# Run tests: the conformance suite, the mutation gate, and the corpus checks.
# Runs WITHOUT the xlsx extra, which is what `pip install rowspec` gives you and
# is therefore the configuration that has to stay green. The exporter's own
# tests skip here; `just test-xlsx` is where they must not.
#
# `--exact` is load-bearing, not tidiness. Plain `uv run` installs what is
# missing and removes nothing, so after one `just test-xlsx` the extra stays in
# the environment and this recipe silently starts running WITH it -- measured:
# `uv run --extra xlsx python -c pass` then `uv run python -c "import
# openpyxl"` succeeds. The configuration under test would then be a local
# accident, and a recipe whose meaning depends on what you ran before it is
# not a check.
test:
    uv run --exact pytest -q

# The exporter, WITH its optional extra. `ROWSPEC_REQUIRE_XLSX=1` turns the
# skip in tests/test_xlsx_export.py into a hard failure, because a test that
# only ever skips is a check that cannot fail -- and this suite would then be
# reporting a pass over an exporter nothing had run.
test-xlsx:
    ROWSPEC_REQUIRE_XLSX=1 uv run --exact --extra xlsx pytest tests/test_xlsx_export.py -q

# The conformance suite alone, driven by the fixture tree
conform:
    cd conformance && uv run python run_cases.py

# The SECOND implementation against the SAME tree. This is a hard gate, not a
# report: it is the only test of whether SPEC.md defines the format or merely
# describes reference/rowspec/. It was met once and then rotted 117 cases
# because nothing ran it while the spec grew -- a check nobody runs is a check
# that cannot fail. If a spec change breaks this, that IS the finding.
conform-alt:
    cd conformance && uv run python run_cases.py rowspec_alt.table

# The mutation gate: the suite must be able to FAIL a broken implementation
mutants:
    cd conformance && uv run python mutants.py

# Validate a file or a directory
run *ARGS:
    uv run python -m rowspec check {{ARGS}}

# Compute a file or a directory, failing on any #REF!
eval *ARGS:
    uv run python -m rowspec eval {{ARGS}}

# Remove build artifacts
clean:
    rm -rf .pytest_cache .ruff_cache dist build **/__pycache__
