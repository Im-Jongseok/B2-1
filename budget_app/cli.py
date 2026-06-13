from __future__ import annotations

import argparse

from datetime import date
from pathlib import Path
from itertools import islice

from .constants import (
    DEFAULT_DATA_DIR,
    TxType, TxField,
    CLI, Prefix, Msg, Prompt,
)
from .service import BudgetService
from .repository import TransactionRepository


""" parser 구축 """
def _build_parser():
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

    return parser

""" 사용자 입력 """
def _input_tx(svc: BudgetService) -> dict:
    tx_date = _ask_date()
    tx_type = _ask_type()
    tx_category = _ask_category(svc)
    tx_amount = _ask_amount()

    return {
        TxField.DATE:     tx_date,
        TxField.TYPE:     tx_type,
        TxField.CATEGORY: tx_category,
        TxField.AMOUNT:   tx_amount,
    }
        
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


""" 거래 추가 """
def cmd_add(args: argparse.Namespace) -> int:

    service = BudgetService(args.data_dir)

    tx = _input_tx(service)
    result = service.add_transaction(**tx)
    print(f'{Prefix.SAVE_OK} {Msg.Info.SAVE_OK.format(result.id)}')

    return 0

""" 거래 목록 출력 """
def cmd_list(args: argparse.Namespace) -> int:
    tx_repo = TransactionRepository(args.data_dir)
    records = list(tx_repo.stream())
    if not records:
        print(f'{Prefix.INFO} {Msg.Info.NO_DATA}')
        return 0
    for record in islice(reversed(records), args.limit):
        _print_tx(record)
    return 0


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