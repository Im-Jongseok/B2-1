from __future__ import annotations

import argparse

from pathlib import Path

from .constants import DEFAULT_DATA_DIR, CLI
from .handlers import cmd_add, cmd_list, cmd_category


# ── Parser ───────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=CLI.PROG,
        description=CLI.DESCRIPTION,
    )
    parser.add_argument(
        CLI.DATA_DIR_OPT,
        type=Path,
        default=DEFAULT_DATA_DIR,
        help=CLI.DATA_DIR_HELP,
    )

    sub = parser.add_subparsers(dest=CLI.COMMAND_DEST, help=CLI.COMMAND_HELP)

    # add
    sub.add_parser(CLI.Command.ADD, help=CLI.Help.ADD)

    # list
    p_list = sub.add_parser(CLI.Command.LIST, help=CLI.Help.LIST)
    p_list.add_argument(CLI.Opt.LIMIT, type=int, default=CLI.Default.LIMIT, help=CLI.Help.LIMIT)

    # category
    p_category = sub.add_parser(CLI.Command.CATEGORY, help=CLI.Help.CATEGORY)
    category_sub = p_category.add_subparsers(dest=CLI.Dest.CATEGORY_CMD)
    category_sub.add_parser(CLI.Command.ADD, help=CLI.Help.CATEGORY_ADD)
    category_sub.add_parser(CLI.Command.LIST, help=CLI.Help.CATEGORY_LIST)
    category_sub.add_parser(CLI.Command.REMOVE, help=CLI.Help.CATEGORY_REMOVE)

    return parser


# ── 진입점 ───────────────────────────────────────────────────

_COMMANDS = {
    CLI.Command.ADD:  cmd_add,
    CLI.Command.LIST: cmd_list,
    CLI.Command.CATEGORY: cmd_category,
}


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    handler = _COMMANDS.get(args.command)
    if handler is None:
        return 1

    return handler(args)


if __name__ == "__main__":
    main()
