"""Command-line interface for wrsrcli.

Every subcommand from SPEC.md is defined with its documented arguments.
Commands that are not built yet report so and exit non-zero.
"""

import argparse
import sys

from . import __version__, commands
from .errors import WrsrcliError


def _not_implemented(command):
    """Build a handler that reports `command` as unimplemented."""

    def handler(args):
        print(f"wrsrcli: '{command}' is not implemented yet.", file=sys.stderr)
        return 1

    return handler


def build_parser():
    parser = argparse.ArgumentParser(
        prog="wrsrcli",
        description=(
            "Inventory, document, and manage Steam Workshop assets for "
            "Workers & Resources: Soviet Republic."
        ),
    )
    parser.add_argument("--version", action="version", version=f"wrsrcli {__version__}")

    subcommands = parser.add_subparsers(dest="command", metavar="<command>")
    subcommands.required = True

    scan = subcommands.add_parser(
        "scan", help="build manifest.json from the local workshop folder"
    )
    scan.set_defaults(func=commands.cmd_scan)

    output_table = subcommands.add_parser(
        "output-table", help="render a searchable HTML table from manifest.json"
    )
    output_table.set_defaults(func=commands.cmd_output_table)

    import_ = subcommands.add_parser(
        "import", help="apply a YAML import list's copy/remove operations"
    )
    import_.add_argument("path", help="path to the YAML import list")
    import_.set_defaults(func=_not_implemented("import"))

    restore = subcommands.add_parser(
        "restore", help="restore files that imports overwrote on this item"
    )
    restore.add_argument("steamid", help="destination workshop item ID")
    restore.set_defaults(func=_not_implemented("restore"))

    rollback = subcommands.add_parser(
        "rollback", help="undo changes this item's import made elsewhere"
    )
    rollback.add_argument("steamid", help="origin workshop item ID")
    rollback.set_defaults(func=_not_implemented("rollback"))

    manual_rerun = subcommands.add_parser(
        "manual-rerun", help="re-apply all tracked import lists"
    )
    manual_rerun.set_defaults(func=_not_implemented("manual-rerun"))

    manual_check = subcommands.add_parser(
        "manual-check", help="flag tracked imports that Steam may have reverted"
    )
    manual_check.set_defaults(func=_not_implemented("manual-check"))

    api = subcommands.add_parser("api", help="set or remove the Steam Web API key")
    api.add_argument("key", nargs="?", help="the Steam Web API key to store")
    api.add_argument(
        "-r", "--remove", action="store_true", help="remove the stored API key"
    )
    api.set_defaults(func=commands.cmd_api)

    path = subcommands.add_parser("path", help="set or auto-detect game/workshop paths")
    path.add_argument("-g", "--game", metavar="PATH", help="set the game install path")
    path.add_argument(
        "-w", "--workshop", metavar="PATH", help="set the workshop content path"
    )
    path.add_argument(
        "-a",
        "--auto-detect",
        action="store_true",
        help="detect both paths from the Windows registry",
    )
    path.set_defaults(func=commands.cmd_path)

    steamcmd = subcommands.add_parser("steamcmd", help="install SteamCMD")
    steamcmd.add_argument(
        "-i", "--install", action="store_true", help="download and install SteamCMD"
    )
    steamcmd.add_argument(
        "-p",
        "--path",
        metavar="PATH",
        help="install to PATH instead of [STEAMPATH]/steamcmd",
    )
    steamcmd.set_defaults(func=commands.cmd_steamcmd)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except WrsrcliError as exc:
        print(f"wrsrcli: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
