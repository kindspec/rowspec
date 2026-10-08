# SPDX-License-Identifier: Apache-2.0 OR MIT
"""rowspec — the reference implementation.

Deliberately boring. The specification and the conformance suite are the
contribution; this exists so there is something to check the suite against, and
so the suite has a second consumer besides its author.
"""

from .csvmode import check_file as check_csv
from .sidecar import find as find_sidecar
from .table import Malformed, canon, evaluate, parse, render, set_cell, structure

__all__ = [
    "Malformed",
    "canon",
    "check_csv",
    "evaluate",
    "find_sidecar",
    "parse",
    "render",
    "set_cell",
    "structure",
]
__version__ = "0.2.0"
