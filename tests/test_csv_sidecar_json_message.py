# SPDX-License-Identifier: Apache-2.0 OR MIT
"""A sidecar that is not valid JSON is refused by content, never by line
number (#232): the message quotes the line where parsing stopped, or says
it stopped at the end of the file.

Unit tests of `rowspec.sidecar`, not conformance cases: the cases for this rule
come from an author who has not read `reference/`.
"""

import os
import re
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")
)

from rowspec.csvmode import check_file  # noqa: E402
from rowspec.table import Malformed  # noqa: E402

PREFIX = "t.csv.rowspec.json is not valid JSON: "


def refusal(tmp_path, sidecar_bytes):
    p = tmp_path / "t.csv"
    p.write_bytes(b"id,v\n1,a\n")
    (tmp_path / "t.csv.rowspec.json").write_bytes(sidecar_bytes)
    with pytest.raises(Malformed) as e:
        check_file(str(p))
    return str(e.value)


@pytest.mark.parametrize(
    "sidecar, rest",
    [
        (
            b'{\n  "key": "id",\n  "order": "v"\n  "order_type": "text"\n}\n',
            "Expecting ',' delimiter in the line '  \"order_type\": \"text\"'",
        ),
        (
            b'{\r\n  "key": "id"\r\n  "order": "v"\r\n}\r\n',
            "Expecting ',' delimiter in the line '  \"order\": \"v\"'",
        ),
        (
            b'{"key": "id",}',
            'Expecting property name enclosed in double quotes in the line \'{"key": "id",}\'',
        ),
        (b"", "Expecting value at the end of the file"),
        (b'{"key": "id"\n\n', "Expecting ',' delimiter at the end of the file"),
    ],
    ids=["multi-line", "crlf", "one-line", "empty", "unclosed"],
)
def test_the_message_quotes_where_parsing_stopped(tmp_path, sidecar, rest):
    assert refusal(tmp_path, sidecar) == PREFIX + rest


def test_a_long_line_is_shown_from_just_before_the_stop(tmp_path):
    side = b'{"key":"id","order":"v","columns":{"population":"number","area":"number" "x":"text"}}'
    msg = refusal(tmp_path, side)
    assert msg == PREFIX + 'Expecting \',\' delimiter in the line \'…:"number" "x":"text"}}\''


def test_no_line_number(tmp_path):
    msg = refusal(tmp_path, b'{\n\n\n\n  "key" "id"\n}\n')
    assert not re.search(r"\bline \d|\(line|column \d|char \d", msg), msg
