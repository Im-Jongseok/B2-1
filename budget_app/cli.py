from __future__ import annotations

import argparse

from pathlib import Path

from .constants import DEFAULT_DATA_DIR, CLI, Files
from .handlers import cmd_add, cmd_list, cmd_category, cmd_search, cmd_update, cmd_delete, cmd_budget, cmd_summary, cmd_export


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

    # add (대화형)
    sub.add_parser(CLI.Command.ADD, help=CLI.Help.ADD)

    # list [--limit N]
    p_list = sub.add_parser(CLI.Command.LIST, help=CLI.Help.LIST)
    p_list.add_argument(CLI.Opt.LIMIT, type=int, default=CLI.Default.LIMIT, help=CLI.Help.LIMIT)

    # search [--from DATE] [--to DATE] [--type TYPE] [--category CAT] [--limit N]
    p_search = sub.add_parser(CLI.Command.SEARCH, help=CLI.Help.SEARCH)
    p_search.add_argument(CLI.Opt.FROM, dest=CLI.Dest.FROM_DATE, help=CLI.Help.FROM_DATE)
    p_search.add_argument(CLI.Opt.TO, dest=CLI.Dest.TO_DATE, help=CLI.Help.TO_DATE)
    p_search.add_argument(CLI.Opt.TYPE, dest=CLI.Dest.TX_TYPE, help=CLI.Help.TX_TYPE)
    p_search.add_argument(CLI.Opt.CATEGORY, help=CLI.Help.CATEGORY_ARG)
    p_search.add_argument(CLI.Opt.LIMIT, type=int, default=CLI.Default.LIMIT, help=CLI.Help.LIMIT)

    # update --id <id> (대화형 필드 선택)
    p_update = sub.add_parser(CLI.Command.UPDATE, help=CLI.Help.UPDATE)
    p_update.add_argument(CLI.Opt.ID, dest=CLI.Dest.TX_ID, required=True, help=CLI.Help.TX_ID)

    # delete --id <id> (확인 후 삭제)
    p_delete = sub.add_parser(CLI.Command.DELETE, help=CLI.Help.DELETE)
    p_delete.add_argument(CLI.Opt.ID, dest=CLI.Dest.TX_ID, required=True, help=CLI.Help.TX_ID)

    # summary --month YYYY-MM [--top N]
    p_summary = sub.add_parser(CLI.Command.SUMMARY, help=CLI.Help.SUMMARY)
    p_summary.add_argument(CLI.Opt.MONTH, dest=CLI.Dest.MONTH, required=True, help=CLI.Help.MONTH)
    p_summary.add_argument(CLI.Opt.TOP, type=int, default=CLI.Default.TOP, help=CLI.Help.TOP)

    # budget set --month YYYY-MM --amount N
    p_budget = sub.add_parser(CLI.Command.BUDGET, help=CLI.Help.BUDGET)
    budget_sub = p_budget.add_subparsers(dest=CLI.Dest.BUDGET_CMD)
    p_budget_set = budget_sub.add_parser(CLI.Command.SET, help=CLI.Help.BUDGET_SET)
    p_budget_set.add_argument(CLI.Opt.MONTH, dest=CLI.Dest.MONTH, required=True, help=CLI.Help.MONTH)
    p_budget_set.add_argument(CLI.Opt.AMOUNT, type=int, required=True, help=CLI.Help.AMOUNT)

    # export --out FILE [--month YYYY-MM | --from DATE --to DATE]
    p_export = sub.add_parser(CLI.Command.EXPORT, help=CLI.Help.EXPORT)
    p_export.add_argument(CLI.Opt.OUT, default=Files.EXPORT, help=CLI.Help.OUT)
    p_export.add_argument(CLI.Opt.MONTH, dest=CLI.Dest.MONTH, default=None, help=CLI.Help.MONTH)
    p_export.add_argument(CLI.Opt.FROM, dest=CLI.Dest.FROM_DATE, default=None, help=CLI.Help.FROM_DATE)
    p_export.add_argument(CLI.Opt.TO, dest=CLI.Dest.TO_DATE, default=None, help=CLI.Help.TO_DATE)


    # category <list|add|remove>
    p_category = sub.add_parser(CLI.Command.CATEGORY, help=CLI.Help.CATEGORY)
    category_sub = p_category.add_subparsers(dest=CLI.Dest.CATEGORY_CMD)
    category_sub.add_parser(CLI.Command.ADD, help=CLI.Help.CATEGORY_ADD)
    category_sub.add_parser(CLI.Command.LIST, help=CLI.Help.CATEGORY_LIST)
    category_sub.add_parser(CLI.Command.REMOVE, help=CLI.Help.CATEGORY_REMOVE)

    return parser


# ── 진입점 ───────────────────────────────────────────────────

_COMMANDS = {
    CLI.Command.ADD:      cmd_add,
    CLI.Command.LIST:     cmd_list,
    CLI.Command.SEARCH:   cmd_search,
    CLI.Command.UPDATE:   cmd_update,
    CLI.Command.DELETE:   cmd_delete,
    CLI.Command.SUMMARY:  cmd_summary,
    CLI.Command.BUDGET:   cmd_budget,
    CLI.Command.EXPORT:   cmd_export,
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
