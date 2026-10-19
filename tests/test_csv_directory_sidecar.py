# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The directory `.rowspec.json`: which entry applies to a file (#190).

An entry naming the file exactly wins over a glob, wherever it is listed.
Without one, a file more than one glob matches is refused rather than given
the first. Every entry is validated, not only the one that applies.

The directory form is rowspec's convenience and outside SPEC.md §13, so these
are unit tests of `rowspec.sidecar`, not conformance cases.
"""

import json
import os
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

from rowspec import cli, sidecar  # noqa: E402
from rowspec.csvmode import check_file  # noqa: E402
from rowspec.table import Malformed  # noqa: E402

CHANNELS = b"id,launched\nr1,2024-01-01\nr2,x\n"
GLOB = {"key": "id"}
EXACT = {"key": "id", "order": "launched", "order_type": "date"}


def write(tmp_path, table, name="channels.csv", data=CHANNELS):
    # json.dumps keeps the insertion order, which is the order under test.
    (tmp_path / ".rowspec.json").write_text(json.dumps(table))
    p = tmp_path / name
    p.write_bytes(data)
    return str(p)


@pytest.mark.parametrize(
    "table",
    [{"*.csv": GLOB, "channels.csv": EXACT}, {"channels.csv": EXACT, "*.csv": GLOB}],
    ids=["exact-after-glob", "exact-before-glob"],
)
def test_an_exact_entry_wins_over_a_glob_in_either_order(tmp_path, table):
    side = sidecar.find(write(tmp_path, table))
    assert (side.order, side.order_type) == ("launched", "date")


def test_the_issue_reproduction_now_checks_the_order_column(tmp_path, capsys):
    write(tmp_path, {"*.csv": GLOB, "channels.csv": EXACT})
    assert cli.main(["check", str(tmp_path / "channels.csv")]) == 1
    assert "order column 'launched' mixes types" in capsys.readouterr().err


def test_two_matching_globs_are_refused_naming_the_file_and_both(tmp_path):
    p = write(tmp_path, {"*.csv": GLOB, "chan*.csv": EXACT})
    with pytest.raises(Malformed) as e:
        check_file(p)
    msg = str(e.value)
    assert "'channels.csv' matches more than one glob" in msg
    assert "'*.csv'" in msg and "'chan*.csv'" in msg


def test_an_exact_entry_settles_two_matching_globs(tmp_path):
    side = sidecar.find(write(tmp_path, {"*.csv": GLOB, "chan*.csv": GLOB, "channels.csv": EXACT}))
    assert side.order == "launched"


def test_one_matching_glob_still_applies(tmp_path):
    side = sidecar.find(write(tmp_path, {"*.csv": EXACT, "*.tsv": GLOB}))
    assert side.order == "launched"


def test_a_malformed_entry_for_another_file_is_reported(tmp_path):
    p = write(tmp_path, {"channels.csv": EXACT, "other.csv": {"oder": "launched"}})
    with pytest.raises(Malformed, match=r"\[other\.csv\]: unknown declaration 'oder'"):
        check_file(p)


def test_a_non_object_entry_for_another_file_is_reported(tmp_path):
    p = write(tmp_path, {"channels.csv": EXACT, "y.csv": None})
    with pytest.raises(Malformed, match=r"\[y\.csv\]: declarations must be a JSON object"):
        check_file(p)


@pytest.mark.parametrize("key", ["sub/channels.csv", "sub\\channels.csv", "*/x.csv"])
def test_a_key_holding_a_path_separator_is_refused_naming_it(tmp_path, key):
    p = write(tmp_path, {"*.csv": GLOB, key: EXACT})
    with pytest.raises(Malformed, match="holds a path separator") as e:
        check_file(p)
    assert repr(key) in str(e.value)


def test_glob_matching_is_case_sensitive_on_every_host(tmp_path, monkeypatch):
    """`fnmatch.fnmatch` folds case through `os.path.normcase`, which is
    lower-casing on Windows; the exact step never folds. Simulating that
    host here: `Channels.csv` must not be taken as a glob matching
    `channels.csv`, which would make two matches and a refusal."""
    p = write(tmp_path, {"*.csv": GLOB, "Channels.csv": EXACT})
    monkeypatch.setattr(os.path, "normcase", str.lower)
    side = sidecar.find(p)
    assert (side.key, side.order) == ("id", None)


def test_a_file_no_entry_matches_has_no_sidecar(tmp_path):
    assert sidecar.find(write(tmp_path, {"other.csv": EXACT, "*.tsv": GLOB})) is None
