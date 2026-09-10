"""The packaging boundary: `reference/` imports the standard library and nothing else.

`AGENTS.md` states the rule in prose. Prose is not enforcement — a lazy
`import openpyxl` inside one function of `reference/rowspec/cli.py` would
satisfy every other check in this repository, ship in the wheel, and quietly
make an xlsx library a requirement of every independent implementation of the
format. That is the failure this file exists to make impossible.

It is deliberately the general rule and not a blocklist of one name. Banning
`openpyxl` by name would pass on the second dependency, and the constraint was
never about xlsx.

The audit walks the tree and parses it, rather than importing it: an import
that only fires on one branch, or inside a function that no test calls, is
exactly the one that would slip past a runtime check.
"""

import ast
import os
import sys
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFERENCE = os.path.join(ROOT, "reference")
EXPORT = os.path.join(ROOT, "export")

# Packages that live in this repository. Importing one of these is not taking a
# dependency: `reference/rowspec_alt` and `reference/rowspec` are shipped by the
# same distribution as the tree that imports them.
INTERNAL = {"rowspec", "rowspec_alt"}


def py_files(root):
    found = []
    for dirpath, dirnames, files in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        found += [os.path.join(dirpath, f) for f in sorted(files) if f.endswith(".py")]
    return sorted(found)


def imported_names(path):
    """Every import in one file, however deeply nested, as top-level module names.

    `ast.walk`, not `tree.body`: a function-local import is still an import,
    and is the shape a forbidden dependency actually arrives in.
    """
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), path)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:  # a relative import is internal
                names.add(node.module.split(".")[0])
    return names


def third_party(root):
    """{file: modules it imports that are neither stdlib nor in this repository}."""
    out = {}
    for path in py_files(root):
        outside = imported_names(path) - sys.stdlib_module_names - INTERNAL
        if outside:
            out[os.path.relpath(path, ROOT)] = sorted(outside)
    return out


def pyproject():
    with open(os.path.join(ROOT, "pyproject.toml"), "rb") as fh:
        return tomllib.load(fh)


# ---------------------------------------------------------------------------
# The audit's own red state. A tree-walking check that silently walks nothing
# reports a pass over an empty set, which is this project's most-repeated
# defect. Both halves are pinned: the walk finds the files, and the audit
# reports a file that offends.
# ---------------------------------------------------------------------------


def test_the_audit_reads_the_tree_it_claims_to_audit():
    found = {os.path.relpath(p, ROOT) for p in py_files(REFERENCE)}
    assert "reference/rowspec/table.py" in found
    assert "reference/rowspec/cli.py" in found
    assert "reference/rowspec_alt/table.py" in found


def test_the_audit_sees_an_import_that_hides_inside_a_function(tmp_path):
    p = tmp_path / "sneaky.py"
    p.write_text(
        "import os\n"
        "def save(t, path):\n"
        "    if path.endswith('.xlsx'):\n"
        "        import openpyxl\n"
        "        return openpyxl.Workbook()\n"
    )
    assert imported_names(str(p)) == {"os", "openpyxl"}
    assert third_party(str(tmp_path)) == {os.path.relpath(str(p), ROOT): ["openpyxl"]}


def test_the_audit_sees_a_from_import_and_ignores_a_relative_one(tmp_path):
    (tmp_path / "a.py").write_text(
        "from openpyxl.workbook import Workbook\nfrom . import export_file\n"
    )
    assert imported_names(str(tmp_path / "a.py")) == {"openpyxl"}


# ---------------------------------------------------------------------------
# The rule itself.
# ---------------------------------------------------------------------------


def test_reference_imports_only_the_standard_library():
    offenders = third_party(REFERENCE)
    assert not offenders, (
        "reference/ must import the standard library and nothing else, because a "
        "dependency here is a dependency every independent implementation of the "
        f"format inherits. Found: {offenders}. Code that needs a dependency goes "
        "in export/, behind an optional extra."
    )


def test_the_exporter_is_where_the_dependency_lives():
    """The other half: the extra is real, and it is real in exactly one place."""
    assert third_party(EXPORT) == {"export/rowspec_xlsx/__init__.py": ["openpyxl"]}, (
        "export/ is the only tree allowed a dependency, and openpyxl is the only "
        "one declared. A second one is a decision, not an import — declare it in "
        "the extra and update this assertion."
    )


# ---------------------------------------------------------------------------
# The packaging seam. `pip install rowspec` must pull no xlsx dependency;
# `pip install rowspec[xlsx]` must pull it AND ship the code that uses it.
# ---------------------------------------------------------------------------


def test_a_plain_install_pulls_no_dependency_at_all():
    assert pyproject()["project"]["dependencies"] == []


def test_the_xlsx_extra_declares_openpyxl():
    extras = pyproject()["project"].get("optional-dependencies", {})
    assert "xlsx" in extras, "`pip install rowspec[xlsx]` installs nothing without this"
    assert any(r.startswith("openpyxl") for r in extras["xlsx"]), extras["xlsx"]


def test_the_extra_ships_the_code_that_needs_it():
    """An extra that installs openpyxl and no exporter is an extra that does nothing."""
    packages = pyproject()["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"]
    assert "export/rowspec_xlsx" in packages
    assert "reference/rowspec" in packages
