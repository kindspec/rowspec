# SPDX-License-Identifier: MIT
"""`rowspec.csvmode`, reading its sidecar through the file the gate names.

The mutation gate's `sidecar` profile measures `sidecar.py`, which is not a
module the runner can be pointed at: the CSV profile checks `csvmode`, and
`csvmode` imports `rowspec.sidecar` by name. So this module loads the file in
`$ROWSPEC_GATE_SIDECAR` AS `rowspec.sidecar` -- under that name, so its
relative `from .table import` resolves -- reloads `csvmode` over it, and
re-exports what the runner calls. No variable, no module: a probe that read
the installed `sidecar.py` instead would agree with itself and every mutant
would survive.
"""

import importlib
import importlib.util
import os
import sys

import rowspec

_spec = importlib.util.spec_from_file_location(
    "rowspec.sidecar", os.environ["ROWSPEC_GATE_SIDECAR"]
)
_sidecar = importlib.util.module_from_spec(_spec)
sys.modules["rowspec.sidecar"] = _sidecar
_spec.loader.exec_module(_sidecar)
rowspec.sidecar = _sidecar

from rowspec import csvmode as _csvmode  # noqa: E402

_csvmode = importlib.reload(_csvmode)
assert _csvmode.sidecar_mod is _sidecar

check_file = _csvmode.check_file
Malformed = _csvmode.Malformed
