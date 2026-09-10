"""`python -m rowspec_xlsx SRC.mdtbl DST.xlsx`.

Not a console script. An entry point declared in `[project.scripts]` is
installed by `pip install rowspec` whether or not the extra was asked for, and
a `rowspec-xlsx` command that can only fail is a worse surface than no command.
"""

import sys


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if len(argv) != 2:
        print("usage: python -m rowspec_xlsx SRC.mdtbl DST.xlsx", file=sys.stderr)
        return 2
    from . import export_file

    print(export_file(argv[0], argv[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
