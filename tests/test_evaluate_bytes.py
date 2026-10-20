# SPDX-License-Identifier: Apache-2.0 OR MIT
"""`evaluate_bytes`: §9.14 decided by the library, from the bytes (#222).

`evaluate` takes text, so a file that is not UTF-8 was refused by whoever
decoded it, the CLI, and the conformance runner could not reach the refusal.
Both implementations now take bytes too, and the runner hands them a
`parse` case's `input.bin`. These are unit tests of the entry point and of
the runner path, over temporary trees; the conformance case lives in
`conformance/cases/`.
"""

import importlib
import json
import os
import re
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONF = os.path.join(ROOT, "conformance")
sys.path.insert(0, os.path.join(ROOT, "reference"))

IMPLS = ["rowspec.table", "rowspec_alt.table"]
GOOD = b"| id | n |\n| --- | --- |\n| r_1 | caf\xc3\xa9 |\n\nkey := id\n"
LATIN1 = GOOD.replace(b"caf\xc3\xa9", b"caf\xe9")
OFFSET = re.compile(r"\b(position|offset|at|line|byte) \d+\b")  # not `byte 0xE9`


@pytest.fixture(params=IMPLS)
def impl(request):
    return importlib.import_module(request.param)


def test_well_formed_bytes_evaluate_as_their_text(impl):
    assert impl.evaluate_bytes(GOOD) == impl.evaluate(GOOD.decode("utf-8"))


def test_a_byte_that_is_not_utf8_is_bad_encoding(impl):
    with pytest.raises(impl.Malformed) as ex:
        impl.evaluate_bytes(LATIN1)
    assert ex.value.refusal == "bad-encoding"
    assert "0xE9" in str(ex.value)
    assert not OFFSET.search(str(ex.value)), str(ex.value)


def test_bad_encoding_is_decided_before_any_line_is_classified(impl):
    """§9.14: before a line is looked at, so a file that is also a lone CR
    and a conflict marker is still `bad-encoding`."""
    with pytest.raises(impl.Malformed) as ex:
        impl.evaluate_bytes(b"<<<<<<< ours\r" + LATIN1)
    assert ex.value.refusal == "bad-encoding"


def test_a_bom_is_still_leading_bom(impl):
    """A BOM is well-formed UTF-8, so it is §9.26, not §9.14."""
    with pytest.raises(impl.Malformed) as ex:
        impl.evaluate_bytes(b"\xef\xbb\xbf" + GOOD)
    assert ex.value.refusal == "leading-bom"


def test_the_reference_names_the_line_as_the_cli_does():
    from rowspec.table import Malformed, evaluate_bytes

    with pytest.raises(Malformed) as ex:
        evaluate_bytes(LATIN1)
    assert str(ex.value) == (
        "not valid UTF-8: the line '| r_1 | caf\\xe9 |' holds byte 0xE9, which is"
        " not part of a valid sequence (invalid continuation byte)"
    )


def _tree(tmp_path, files, expect):
    case = tmp_path / "tree" / "parse" / "c"
    case.mkdir(parents=True)
    for name, data in files.items():
        (case / name).write_bytes(data)
    (case / "expect.json").write_text(json.dumps(expect))
    return tmp_path / "tree"


def _run(impl, root):
    return subprocess.run(
        [sys.executable, "run_cases.py", impl, str(root), "--min-cases", "1"],
        cwd=CONF,
        capture_output=True,
        text=True,
    )


REFUSED = {"kind": "parse", "accept": False, "refusal": "bad-encoding"}


@pytest.mark.parametrize("name", IMPLS)
def test_the_runner_hands_input_bin_to_evaluate_bytes(tmp_path, name):
    root = _tree(tmp_path, {"input.bin": LATIN1}, REFUSED)
    r = _run(name, root)
    assert r.returncode == 0, r.stdout + r.stderr


@pytest.mark.parametrize("name", IMPLS)
def test_input_bin_that_is_accepted_fails_a_refusing_case(tmp_path, name):
    """The path can fail: well-formed bytes are accepted, and a case that
    says `bad-encoding` over them is a failure, exit 1."""
    root = _tree(tmp_path, {"input.bin": GOOD}, REFUSED)
    r = _run(name, root)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "expected refusal bad-encoding, got accept" in r.stdout + r.stderr


def test_a_case_holding_both_artifacts_fails(tmp_path):
    root = _tree(
        tmp_path,
        {"input.bin": LATIN1, "input.mdtbl": GOOD},
        REFUSED,
    )
    r = _run("rowspec.table", root)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "both input.mdtbl and input.bin" in r.stdout + r.stderr


def test_an_implementation_without_evaluate_bytes_fails_the_case(tmp_path):
    """Not a pass, and not a decode by the runner on its behalf: the
    runner never decodes `input.bin` itself."""
    shim = os.path.join(CONF, "_no_bytes.py")
    with open(shim, "w") as fh:
        fh.write(
            "import sys, os\n"
            "sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'reference'))\n"
            "from rowspec.table import Malformed, evaluate\n"
        )
    try:
        root = _tree(tmp_path, {"input.bin": LATIN1}, REFUSED)
        r = _run("_no_bytes", root)
    finally:
        os.remove(shim)
    assert r.returncode == 1, r.stdout + r.stderr
