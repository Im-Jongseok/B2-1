from __future__ import annotations

import argparse

from datetime import date
from itertools import islice
from pathlib import Path

from .constants import (
    DEFAULT_DATA_DIR,
    TxType, TxField,
    CLI, Prefix, Msg, Prompt,
)
from .repository import TransactionRepository
from .service import BudgetService


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

    sub.add_parser(CLI.Command.ADD, help=CLI.Help.ADD)

    p_list = sub.add_parser(CLI.Command.LIST, help=CLI.Help.LIST)
    p_list.add_argument(CLI.Opt.LIMIT, type=int, default=CLI.Default.LIMIT, help=CLI.Help.LIMIT)

    return parser


# ── 대화형 입력 헬퍼 ─────────────────────────────────────────

def _ask_date() -> str:
    while True:
        raw = input(Prompt.DATE).strip()
        try:
            date.fromisoformat(raw)
            return raw
        except ValueError:
            print(f'{Prefix.ERROR} {Msg.Error.DATE_FORMAT}')
            print(f'{Prefix.HINT} {Msg.Hint.DATE_FORMAT}')


def _ask_type() -> str:
    while True:
        raw = input(Prompt.TYPE).strip().lower()
        if raw in TxType.ALL:
            return raw
        print(f'{Prefix.ERROR} {Msg.Error.TYPE_INVALID}')


def _ask_category(svc: BudgetService) -> str:
    categories = svc.category_repo.list_categories()
    while True:
        print(f'{Prefix.CATEGORIES} {", ".join(categories)}')
        raw = input(Prompt.CATEGORY).strip().lower()
        if raw in categories:
            return raw
        print(f'{Prefix.ERROR} {Msg.Error.CATEGORY_NOT_FOUND.format(raw)}')
        print(f'{Prefix.HINT} {Msg.Hint.CATEGORY_ADD}')


def _ask_amount() -> int:
    while True:
        raw = input(Prompt.AMOUNT).strip()
        try:
            amount = int(raw)
            if amount <= 0:
                print(f'{Prefix.ERROR} {Msg.Error.AMOUNT_NOT_POS}')
                continue
            return amount
        except ValueError:
            print(f'{Prefix.ERROR} {Msg.Error.AMOUNT_NOT_NUM}')


def _input_tx(svc: BudgetService) -> dict:
    """add 명령에 필요한 필드를 순차적으로 입력받아 dict로 반환한다."""
    return {
        TxField.DATE:     _ask_date(),
        TxField.TYPE:     _ask_type(),
        TxField.CATEGORY: _ask_category(svc),
        TxField.AMOUNT:   _ask_amount(),
    }


# ── 출력 헬퍼 ────────────────────────────────────────────────

def _print_tx(r: dict) -> None:
    tx_type = TxType.INCOME_KO if r[TxField.TYPE] == TxType.INCOME else TxType.EXPENSE_KO
    amount_str = f"{r[TxField.AMOUNT]:,}원"
    print(
        f"  {r[TxField.ID]} | "
        f"{r[TxField.DATE]} | "
        f"{tx_type} | "
        f"{r[TxField.CATEGORY]:<12} | "
        f"{amount_str:>12}"
    )


# ── 커맨드 핸들러 ─────────────────────────────────────────────

def cmd_add(args: argparse.Namespace) -> int:
    service = BudgetService(args.data_dir)
    tx = _input_tx(service)
    result = service.add_transaction(**tx)
    print(f'{Prefix.SAVE_OK} {Msg.Info.SAVE_OK.format(result.id)}')
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    tx_repo = TransactionRepository(args.data_dir)
    records = list(tx_repo.stream())
    if not records:
        print(f'{Prefix.INFO} {Msg.Info.NO_DATA}')
        return 0
    for record in islice(reversed(records), args.limit):
        _print_tx(record)
    return 0


# ── 진입점 ───────────────────────────────────────────────────

_COMMANDS = {
    CLI.Command.ADD:  cmd_add,
    CLI.Command.LIST: cmd_list,
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
