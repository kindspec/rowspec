# SPDX-License-Identifier: Apache-2.0 OR MIT
"""A CSV field longer than the csv module's default limit of 131,072
characters is checked like any other (#235).

SPEC.md §9: "Recognition is total" and "This list is complete". No refusal
covers a long field, and §13 takes record boundaries from RFC 4180, which
sets no length limit. So CSV mode lifts the reader's limit rather than
refusing, and it used to crash with `_csv.Error`.

Unit tests of `rowspec.csvmode`, not conformance cases: the cases for this rule
come from an author who has not read `reference/`.
"""

import csv
import os
import sys
import threading

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

from rowspec import cli, csvmode  # noqa: E402
from rowspec.csvmode import check_file, check_text  # noqa: E402
from rowspec.table import Malformed  # noqa: E402

BIG = "x" * 200_000


def write(tmp_path, data):
    p = tmp_path / "t.csv"
    p.write_bytes(data.encode("utf-8") if isinstance(data, str) else data)
    return str(p)


def test_a_long_field_is_accepted(tmp_path):
    assert check_file(write(tmp_path, f"id,v\n1,{BIG}\n2,b\n")) == []


def test_a_long_quoted_field_is_accepted(tmp_path):
    assert check_file(write(tmp_path, f'id,v\n1,"{BIG}\nmore"\n')) == []


def test_a_long_field_does_not_hide_a_later_refusal(tmp_path):
    findings = check_file(write(tmp_path, f"id,v\n1,{BIG}\n2,b,c\n"))
    assert [f.rule for f in findings] == ["field-count"]
    assert findings[0].message.startswith("row id='2' has 3 field(s)")


def test_a_long_field_holding_a_stray_quote_names_its_row(tmp_path):
    findings = check_file(write(tmp_path, f'id,v\n1,{BIG}"b\n'))
    assert [f.rule for f in findings] == ["stray-quote"]
    assert findings[0].message.startswith("row id='1': the field 'xxx"), findings[0].message


def test_a_long_field_with_a_byte_that_is_not_utf8_names_the_row(tmp_path):
    with pytest.raises(Malformed) as e:
        check_file(write(tmp_path, f"id,v\n1,{BIG}".encode() + b"\xff\n"))
    assert str(e.value).startswith("row id='1': the field "), str(e.value)


def test_check_text_accepts_a_long_field():
    assert check_text(f"id,v\n1,{BIG}\n") == []


def test_the_cli_checks_it(tmp_path, capsys):
    write(tmp_path, f"id,v\n1,{BIG}\n")
    assert cli.main(["check", str(tmp_path)]) == 0


def test_the_csv_modules_limit_is_put_back(tmp_path):
    # Set a known limit first: a call that leaked the lifted one would
    # otherwise compare it with itself.
    old = csv.field_size_limit(131_072)
    try:
        check_file(write(tmp_path, f"id,v\n1,{BIG}\n"))
        assert csv.field_size_limit() == 131_072
        check_text(f"id,v\n1,{BIG}\n")
        assert csv.field_size_limit() == 131_072
    finally:
        csv.field_size_limit(old)


def test_a_field_of_a_few_megabytes_is_accepted():
    # Pins how far the limit is lifted: a limit of 2**20 would refuse it.
    assert check_text("id,v\n1," + "x" * 3_000_000 + "\n") == []


def test_the_limit_is_put_back_after_a_refusal():
    old = csv.field_size_limit(131_072)
    try:
        with pytest.raises(Malformed, match="no table"):
            check_text("")
        assert csv.field_size_limit() == 131_072
    finally:
        csv.field_size_limit(old)


def test_two_threads_do_not_put_the_limit_back_out_of_order():
    """The first thread to leave must not restore the default while a
    second is still inside, and the second must not leave the lifted
    limit behind. Without the lock both happen: the second thread enters
    while the first holds the limit, sees the default once the first
    leaves, and on leaving restores the lifted limit it found on entry."""
    old = csv.field_size_limit(131_072)
    first_in, release_first, first_out, second_in = (threading.Event() for _ in range(4))
    seen = []

    def first():
        with csvmode._no_field_limit():
            first_in.set()
            release_first.wait(5)
        first_out.set()

    def second():
        with csvmode._no_field_limit():
            second_in.set()
            first_out.wait(5)
            seen.append(csv.field_size_limit())

    try:
        a = threading.Thread(target=first)
        a.start()
        assert first_in.wait(5)
        b = threading.Thread(target=second)
        b.start()
        # With the lock the second thread is still waiting to enter.
        second_in.wait(0.5)
        release_first.set()
        a.join(5)
        b.join(5)
        assert seen == [csvmode._FIELD_LIMIT]
        assert csv.field_size_limit() == 131_072
    finally:
        release_first.set()
        csv.field_size_limit(old)


def test_a_check_inside_a_lifted_window_does_not_deadlock():
    # The lock is re-entrant: a check made while the limit is already
    # lifted on the same thread, as a caller wrapping several may do,
    # must not wait on itself. Run in a thread so a deadlock fails the
    # test instead of hanging the suite.
    done = []

    def nested():
        with csvmode._no_field_limit():
            done.append(check_text(f"id,v\n1,{BIG}\n"))

    t = threading.Thread(target=nested, daemon=True)
    t.start()
    t.join(5)
    stuck = t.is_alive()
    if stuck:
        # A plain Lock deadlocked: any thread may release one, and doing so
        # lets the stuck thread finish, so the rest of the suite still runs.
        csvmode._FIELD_LIMIT_LOCK.release()
        t.join(5)
    assert not stuck, "a check inside a lifted window waited on its own lock"
    assert done == [[]]
