from __future__ import annotations

import argparse

from datetime import date
from itertools import islice

from .constants import (
    TxType, TxField,
    Prefix, Msg, Prompt, CLI
)
from .repository import TransactionRepository, CategoryRepository
from .service import BudgetService


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
        print(f'{Prefix.HINT} {Msg.Hint.TYPE_INVALID}')


def _ask_new_category(category_repo: CategoryRepository) -> str:
    while True:
        raw = input(Prompt.CATEGORY).strip().lower()
        if not raw:
            print(f'{Prefix.ERROR} {Msg.Error.CATEGORY_EMPTY}')
            continue
        if category_repo.exists(raw):
            print(f'{Prefix.ERROR} {Msg.Error.CATEGORY_ALREADY_EXIST.format(raw)}')
            print(f'{Prefix.HINT} {Msg.Hint.CATEGORY_LIST}')
            continue
        return raw


def _ask_category(category_repo: CategoryRepository) -> str:
    categories = category_repo.list_categories()
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
                print(f'{Prefix.HINT} {Msg.Hint.AMOUNT}')
                continue
            return amount
        except ValueError:
            print(f'{Prefix.ERROR} {Msg.Error.AMOUNT_NOT_NUM}')
            print(f'{Prefix.HINT} {Msg.Hint.AMOUNT}')


def _input_tx(svc: BudgetService) -> dict:
    """add 명령에 필요한 필드를 순차적으로 입력받아 dict로 반환한다."""
    return {
        TxField.DATE:     _ask_date(),
        TxField.TYPE:     _ask_type(),
        TxField.CATEGORY: _ask_category(svc.category_repo),
        TxField.AMOUNT:   _ask_amount(),
    }


# ── 출력 헬퍼 ────────────────────────────────────────────────

def _print_tx(r: dict) -> None:
    tx_type = TxType.INCOME_KO if r[TxField.TYPE] == TxType.INCOME else TxType.EXPENSE_KO
    amount_str = f"{r[TxField.AMOUNT]:,}원"
    print(
        f"{r[TxField.ID]} | "
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
    print(f'{Prefix.OK.format(Prefix.SAVE)} {Msg.Info.SAVE_OK.format(result.id)}')
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

def cmd_category(args: argparse.Namespace) -> int:
    category_repo = CategoryRepository(args.data_dir)

    if args.category_cmd == CLI.Command.LIST:
        categories = category_repo.list_categories()
        print(f'{Prefix.CATEGORIES} ({len(categories)})')
        for c in categories:
            print(f"{c}")

    elif args.category_cmd == CLI.Command.ADD:
        category = _ask_new_category(category_repo)
        category_repo.add(category)
        print(f'{Prefix.OK.format(Prefix.SAVE)} {CLI.Command.CATEGORY}={category}')
    
    elif args.category_cmd == CLI.Command.REMOVE:
        tx_repo = TransactionRepository(args.data_dir)
        category = _ask_category(category_repo)

        # 거래에 카테고리가 사용되고 있어 삭제 차단
        has_tx = any(r[TxField.CATEGORY] == category for r in tx_repo.stream())
        if has_tx:
            print(f'{Prefix.ERROR} {Msg.Error.CATEGORY_USED.format(category)}')
            print(f'{Prefix.HINT} {Msg.Hint.CATEGORY_USED}')
            return 1

        if category_repo.remove(category):
            print(f'{Prefix.OK.format(Prefix.REMOVE)} {CLI.Command.CATEGORY}={category}')
        else:
            print(f'{Prefix.ERROR} {Msg.Error.CATEGORY_NOT_FOUND.format(category)}')
    
    else:
        print(f'{Prefix.ERROR} {Msg.Error.CATEGORY_INVALID_CMD}')
        print(f'{Prefix.HINT} {Msg.Hint.CATEGORY_INVALID_CMD}')
        return 1

    return 0 
