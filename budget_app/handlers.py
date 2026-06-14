from __future__ import annotations

import argparse

from datetime import date
from itertools import islice

from .constants import (
    TxType, TxField,
    Prefix, Msg, Prompt, CLI,
    Confirm, Fmt,
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
        print(f'{Prefix.CATEGORIES} {Fmt.LIST_SEP.join(categories)}')
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


def _ask_update_fields(category_repo: CategoryRepository) -> dict:
    FIELD_HANDLERS = {
        TxField.DATE:     _ask_date,
        TxField.TYPE:     _ask_type,
        TxField.CATEGORY: lambda: _ask_category(category_repo),
        TxField.AMOUNT:   _ask_amount,
    }
    raw = input(Prompt.UPDATE_FIELDS).strip().lower()
    selected = [f for f in raw.split() if f in FIELD_HANDLERS]
    return {field: FIELD_HANDLERS[field]() for field in selected}


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
    amount_str = f"{r[TxField.AMOUNT]:,}{Fmt.CURRENCY}"
    print(
        f"{r[TxField.ID]} | "
        f"{r[TxField.DATE]} | "
        f"{tx_type} | "
        f"{r[TxField.CATEGORY]:<12} | "
        f"{amount_str:>12}"
    )


# ── 필터 헬퍼 ────────────────────────────────────────────────

def _matches_filter(
    r: dict,
    from_date: str | None,
    to_date: str | None,
    tx_type: str | None,
    category: str | None,
) -> bool:
    # ISO 날짜 문자열은 사전순 비교로 대소 비교가 가능
    if from_date and r[TxField.DATE] < from_date:
        return False
    if to_date and r[TxField.DATE] > to_date:
        return False
    if tx_type and r[TxField.TYPE] != tx_type:
        return False
    if category and r[TxField.CATEGORY] != category:
        return False
    return True


# ── 커맨드 핸들러 ─────────────────────────────────────────────

def cmd_add(args: argparse.Namespace) -> int:
    service = BudgetService(args.data_dir)
    tx = _input_tx(service)
    result = service.add_transaction(**tx)
    print(f'{Prefix.OK.format(Prefix.SAVE)} {Msg.Info.SAVE_OK.format(result.id)}')
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    tx_repo = TransactionRepository(args.data_dir)
    records = [
        r for r in tx_repo.stream()
        if _matches_filter(r, args.from_date, args.to_date, args.tx_type, args.category)
    ]
    if not records:
        print(f'{Prefix.INFO} {Msg.Info.NO_DATA}')
        return 0
    for record in reversed(records):
        _print_tx(record)
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    tx_repo = TransactionRepository(args.data_dir)

    record = tx_repo.find(args.tx_id)
    if record is None:
        print(f'{Prefix.ERROR} {Msg.Error.TX_NOT_FOUND.format(args.tx_id)}')
        print(f'{Prefix.HINT} {Msg.Hint.TX_ID}')
        return 1

    _print_tx(record)

    category_repo = CategoryRepository(args.data_dir)
    fields = _ask_update_fields(category_repo)

    if not fields:
        print(f'{Prefix.ERROR} {Msg.Error.NO_CHANGES}')
        return 1

    tx_repo.update(args.tx_id, fields)
    print(f'{Prefix.OK.format(Prefix.SAVE)} {TxField.ID}{Fmt.KV_SEP}{args.tx_id}')
    _print_tx({**record, **fields})
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    tx_repo = TransactionRepository(args.data_dir)

    record = tx_repo.find(args.tx_id)
    if record is None:
        print(f'{Prefix.ERROR} {Msg.Error.TX_NOT_FOUND.format(args.tx_id)}')
        print(f'{Prefix.HINT} {Msg.Hint.TX_ID}')
        return 1

    _print_tx(record)
    confirm = input(Prompt.DELETE_CONFIRM).strip().lower()
    if confirm == Confirm.NO:
        print(f'{Prefix.INFO} {Msg.Info.DELETE_CANCELLED}')
        return 0
    elif confirm != Confirm.YES:
        print(f'{Prefix.ERROR} {Msg.Error.CONFIRM_INVALID}')
        print(f'{Prefix.HINT} {Msg.Hint.CONFIRM_INVALID}')
        return 1


    tx_repo.delete(args.tx_id)
    print(f'{Prefix.OK.format(Prefix.REMOVE)} {TxField.ID}{Fmt.KV_SEP}{args.tx_id}')
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
            print(f'{c}')

    elif args.category_cmd == CLI.Command.ADD:
        category = _ask_new_category(category_repo)
        category_repo.add(category)
        print(f'{Prefix.OK.format(Prefix.SAVE)} {CLI.Command.CATEGORY}{Fmt.KV_SEP}{category}')
    
    elif args.category_cmd == CLI.Command.REMOVE:
        tx_repo = TransactionRepository(args.data_dir)
        category = _ask_category(category_repo)

        # (A) 거래에 카테고리가 사용되고 있어 삭제 차단
        has_tx = any(r[TxField.CATEGORY] == category for r in tx_repo.stream())
        if has_tx:
            print(f'{Prefix.ERROR} {Msg.Error.CATEGORY_USED.format(category)}')
            print(f'{Prefix.HINT} {Msg.Hint.CATEGORY_USED}')
            return 1

        category_repo.remove(category)
        print(f'{Prefix.OK.format(Prefix.REMOVE)} {CLI.Command.CATEGORY}{Fmt.KV_SEP}{category}')
    
    else:
        print(f'{Prefix.ERROR} {Msg.Error.CATEGORY_INVALID_CMD}')
        print(f'{Prefix.HINT} {Msg.Hint.CATEGORY_INVALID_CMD}')
        return 1

    return 0 
