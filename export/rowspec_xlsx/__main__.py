# SPDX-License-Identifier: Apache-2.0 OR MIT
"""`python -m rowspec_xlsx [--values] SRC.mdtbl DST.xlsx`.

Not a console script. An entry point declared in `[project.scripts]` is
installed by `pip install rowspec` whether or not the extra was asked for, and
a `rowspec-xlsx` command that can only fail is a worse surface than no command.
"""

import argparse
import sys


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="python -m rowspec_xlsx",
        description="Export a .mdtbl to .xlsx. Computed cells are formulas unless --values.",
    )
    p.add_argument("src", metavar="SRC.mdtbl")
    p.add_argument("dst", metavar="DST.xlsx")
    p.add_argument(
        "--values",
        action="store_true",
        help="write rowspec eval's values instead of formulas, each #REF! as an error cell",
    )
    try:
        args = p.parse_args(argv)
    except SystemExit as e:
        return e.code
    from . import NotExpressible, export_file

    try:
        print(export_file(args.src, args.dst, values=args.values))
    except NotExpressible as e:
        print(f"not exported: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
