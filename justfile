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

# Run tests: the conformance suite, the mutation gate, and the corpus checks
test:
    uv run pytest -q

# The conformance suite alone, driven by the fixture tree
conform:
    cd conformance && uv run python run_cases.py

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
