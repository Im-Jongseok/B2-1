from __future__ import annotations

import argparse
from itertools import islice

from .constants import (
    TxType, TxField, TxId, BudgetField, RecurringField, SummaryKey,
    Prefix, Msg, Prompt, CLI,
    Confirm, Fmt, ColWidth,
)
from .decorators import handle_errors
from .formatter import ljust_display, print_tx, print_tx_header
from .service import BudgetService


# ── 대화형 입력 헬퍼 ─────────────────────────────────────────────

def _ask_date() -> str:
    from datetime import date as _date
    while True:
        raw = input(Prompt.DATE).strip()
        try:
            _date.fromisoformat(raw)
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


def _ask_new_category(category_repo) -> str:
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


def _ask_category(category_repo) -> str:
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


def _ask_day() -> int:
    while True:
        raw = input(Prompt.DAY).strip()
        try:
            day = int(raw)
            if 1 <= day <= 31:
                return day
            print(f'{Prefix.ERROR} {Msg.Error.DAY_INVALID}')
            print(f'{Prefix.HINT} {Msg.Hint.DAY}')
        except ValueError:
            print(f'{Prefix.ERROR} {Msg.Error.DAY_INVALID}')
            print(f'{Prefix.HINT} {Msg.Hint.DAY}')


def _ask_update_recurring_fields(category_repo) -> dict:
    FIELD_HANDLERS = {
        RecurringField.TYPE:     _ask_type,
        RecurringField.DAY:      _ask_day,
        RecurringField.CATEGORY: lambda: _ask_category(category_repo),
        RecurringField.AMOUNT:   _ask_amount,
    }
    raw = input(Prompt.UPDATE_RECURRING_FIELDS).strip().lower()
    tokens = raw.split()
    selected = [f for f in tokens if f in FIELD_HANDLERS]
    unknown  = [f for f in tokens if f not in FIELD_HANDLERS]
    if unknown:
        print(f'{Prefix.WARN} {Msg.Warn.UNKNOWN_FIELD.format(Fmt.LIST_SEP.join(unknown))}')
    return {field: FIELD_HANDLERS[field]() for field in selected}


def _ask_update_fields(category_repo) -> dict:
    FIELD_HANDLERS = {
        TxField.DATE:     _ask_date,
        TxField.TYPE:     _ask_type,
        TxField.CATEGORY: lambda: _ask_category(category_repo),
        TxField.AMOUNT:   _ask_amount,
    }
    raw = input(Prompt.UPDATE_FIELDS).strip().lower()
    tokens = raw.split()
    selected = [f for f in tokens if f in FIELD_HANDLERS]
    unknown  = [f for f in tokens if f not in FIELD_HANDLERS]
    if unknown:
        print(f'{Prefix.WARN} {Msg.Warn.UNKNOWN_FIELD.format(Fmt.LIST_SEP.join(unknown))}')
    return {field: FIELD_HANDLERS[field]() for field in selected}


def _input_tx(svc: BudgetService) -> dict:
    return {
        TxField.DATE:     _ask_date(),
        TxField.TYPE:     _ask_type(),
        TxField.CATEGORY: _ask_category(svc.category_repo),
        TxField.AMOUNT:   _ask_amount(),
    }


# ── update / delete 공통 흐름 ─────────────────────────────────────

def _run_update(record: dict, print_fn, ask_fn, update_fn, id_field: str, id_val: str) -> int:
    print(f'{Msg.Info.BEFORE}')
    print(ColWidth.SEP_LINE)
    print_fn(record)
    print(ColWidth.SEP_LINE)
    fields = ask_fn()
    if not fields:
        print(f'{Prefix.ERROR} {Msg.Error.NO_CHANGES}')
        return 1
    update_fn(id_val, fields)
    print(f'{Prefix.DONE.format(Prefix.SAVE)} {id_field}{Fmt.KV_SEP}{id_val}')
    print(f'{Msg.Info.AFTER}')
    print(ColWidth.SEP_LINE)
    print_fn({**record, **fields})
    print(ColWidth.SEP_LINE)
    return 0


def _run_delete(record: dict, print_fn, delete_fn, id_field: str, id_val: str) -> int:
    print_fn(record)
    confirm = input(Prompt.DELETE_CONFIRM).strip().lower()
    if confirm == Confirm.NO:
        print(f'{Prefix.INFO} {Msg.Info.DELETE_CANCELLED}')
        return 0
    elif confirm != Confirm.YES:
        print(f'{Prefix.ERROR} {Msg.Error.CONFIRM_INVALID}')
        print(f'{Prefix.HINT} {Msg.Hint.CONFIRM_INVALID}')
        return 1
    delete_fn(id_val)
    print(f'{Prefix.DONE.format(Prefix.REMOVE)} {id_field}{Fmt.KV_SEP}{id_val}')
    return 0


# ── 반복 내역 헬퍼 ────────────────────────────────────────────────

def _print_recurring(r: dict) -> None:
    type_ko = TxType.INCOME_KO if r[RecurringField.TYPE] == TxType.INCOME else TxType.EXPENSE_KO
    day_str = Fmt.MONTHLY_DAY.format(f"{r[RecurringField.DAY]:2}")
    print(
        f"{r[RecurringField.ID]}{Fmt.COL_SEP}"
        f"{day_str}{Fmt.COL_SEP}"
        f"{type_ko}{Fmt.COL_SEP}"
        f"{ljust_display(r[RecurringField.CATEGORY], 12)}{Fmt.COL_SEP}"
        f"{r[RecurringField.AMOUNT]:,}{Fmt.CURRENCY}"
    )


# ── 커맨드 핸들러 ─────────────────────────────────────────────────

@handle_errors
def cmd_add(args: argparse.Namespace) -> int:
    svc = BudgetService(args.data_dir)
    if args.recurring:
        tx_type  = _ask_type()
        category = _ask_category(svc.category_repo)
        day      = _ask_day()
        amount   = _ask_amount()
        rx = svc.add_recurring(tx_type, day, category, amount)
        _print_recurring(rx.to_dict())
        return 0
    tx = _input_tx(svc)
    result = svc.add_transaction(**tx)
    print(f'{Prefix.DONE.format(Prefix.SAVE)} {Msg.Info.SAVE_OK.format(result.id)}')
    print(ColWidth.SEP_LINE)
    print_tx(result.to_dict())
    print(ColWidth.SEP_LINE)
    return 0


@handle_errors
def cmd_list(args: argparse.Namespace) -> int:
    svc = BudgetService(args.data_dir)
    if args.recurring:
        records = svc.list_recurring()
        if not records:
            print(f'{Prefix.INFO} {Msg.Info.NO_DATA}')
            return 0
        print(f'{Prefix.INFO} {Msg.Info.COUNT.format(len(records))}')
        for r in records:
            _print_recurring(r)
        return 0

    records = svc.list_transactions()
    if not records:
        print(f'{Prefix.INFO} {Msg.Info.NO_DATA}')
        return 0
    print(f'{Prefix.INFO} {Msg.Info.COUNT.format(len(records))}')
    print_tx_header()
    for record in islice(reversed(records), args.limit):
        print_tx(record)
    return 0


@handle_errors
def cmd_apply(args: argparse.Namespace) -> int:
    svc = BudgetService(args.data_dir)
    created, skipped = svc.apply_recurring(args.month)
    msg = Msg.Info.APPLY_RESULT.format(args.month, created)
    if skipped:
        msg += f', 중복={skipped}'
    print(f'{Prefix.DONE.format(Prefix.SAVE)} {msg}')
    return 0


@handle_errors
def cmd_search(args: argparse.Namespace) -> int:
    svc = BudgetService(args.data_dir)
    records = svc.search_transactions(args.from_date, args.to_date, args.tx_type, args.category)
    if not records:
        print(f'{Prefix.INFO} {Msg.Info.NO_DATA}')
        return 0
    print(f'{Prefix.INFO} {Msg.Info.COUNT.format(len(records))}')
    print_tx_header()
    for record in reversed(records):
        print_tx(record)
    return 0


@handle_errors
def cmd_update(args: argparse.Namespace) -> int:
    svc = BudgetService(args.data_dir)

    if args.tx_id.startswith(TxId.RX_PREFIX):
        record = svc.find_recurring(args.tx_id)
        if record is None:
            print(f'{Prefix.ERROR} {Msg.Error.RECURRING_NOT_FOUND.format(args.tx_id)}')
            print(f'{Prefix.HINT} {Msg.Hint.RECURRING_ID}')
            return 1
        return _run_update(record, _print_recurring,
                           lambda: _ask_update_recurring_fields(svc.category_repo),
                           svc.update_recurring, RecurringField.ID, args.tx_id)

    record = svc.find_transaction(args.tx_id)
    if record is None:
        print(f'{Prefix.ERROR} {Msg.Error.TX_NOT_FOUND.format(args.tx_id)}')
        print(f'{Prefix.HINT} {Msg.Hint.TX_ID}')
        return 1
    return _run_update(record, print_tx,
                       lambda: _ask_update_fields(svc.category_repo),
                       svc.update_transaction, TxField.ID, args.tx_id)


@handle_errors
def cmd_delete(args: argparse.Namespace) -> int:
    svc = BudgetService(args.data_dir)

    if args.tx_id.startswith(TxId.RX_PREFIX):
        record = svc.find_recurring(args.tx_id)
        if record is None:
            print(f'{Prefix.ERROR} {Msg.Error.RECURRING_NOT_FOUND.format(args.tx_id)}')
            print(f'{Prefix.HINT} {Msg.Hint.RECURRING_ID}')
            return 1
        return _run_delete(record, _print_recurring,
                           svc.delete_recurring, RecurringField.ID, args.tx_id)

    record = svc.find_transaction(args.tx_id)
    if record is None:
        print(f'{Prefix.ERROR} {Msg.Error.TX_NOT_FOUND.format(args.tx_id)}')
        print(f'{Prefix.HINT} {Msg.Hint.TX_ID}')
        return 1
    return _run_delete(record, print_tx,
                       svc.delete_transaction, TxField.ID, args.tx_id)


@handle_errors
def cmd_summary(args: argparse.Namespace) -> int:
    svc  = BudgetService(args.data_dir)
    data = svc.get_summary(args.month, args.top)

    if data[SummaryKey.INCOME_TOTAL] == 0 and data[SummaryKey.EXPENSE_TOTAL] == 0:
        print(f'{Prefix.INFO} {Msg.Info.NO_DATA}')
        return 0

    print(f'{Prefix.SUMMARY.format(args.month)}')
    print(f'{Msg.Info.INCOME_TOTAL}: {data[SummaryKey.INCOME_TOTAL]:,}{Fmt.CURRENCY}')
    print(f'{Msg.Info.EXPENSE_TOTAL}: {data[SummaryKey.EXPENSE_TOTAL]:,}{Fmt.CURRENCY}')
    print(f'{Msg.Info.BALANCE}: {data[SummaryKey.BALANCE]:,}{Fmt.CURRENCY}')

    if data[SummaryKey.TOP_EXPENSE]:
        print(f'\n{Prefix.TOP_EXPENSE.format(args.top)}')
        for i, (cat, amt) in enumerate(data[SummaryKey.TOP_EXPENSE], 1):
            print(f'{i}) {ljust_display(cat, 12)} {amt:,}{Fmt.CURRENCY}')

    budget = data[SummaryKey.BUDGET]
    if budget is not None:
        usage = data[SummaryKey.EXPENSE_TOTAL] / budget * 100
        print(f'\n{Prefix.BUDGET_SECTION}')
        print(f'{Msg.Info.BUDGET_AMOUNT}: {budget:,}{Fmt.CURRENCY}')
        print(f'{Msg.Info.BUDGET_USAGE}: {data[SummaryKey.EXPENSE_TOTAL]:,}{Fmt.CURRENCY} ({usage:.1f}{Fmt.PERCENT})')
        if data[SummaryKey.EXPENSE_TOTAL] > budget:
            over = data[SummaryKey.EXPENSE_TOTAL] - budget
            print(f'{Prefix.WARN} {Msg.Warn.BUDGET_EXCEEDED.format(f"{over:,}")}')

    return 0


@handle_errors
def cmd_budget(args: argparse.Namespace) -> int:
    svc = BudgetService(args.data_dir)

    if args.budget_cmd == CLI.Command.SET:
        svc.set_budget(args.month, args.amount)
        print(
            f'{Prefix.DONE.format(Prefix.SAVE)} '
            f'{BudgetField.MONTH}{Fmt.KV_SEP}{args.month} '
            f'{BudgetField.AMOUNT}{Fmt.KV_SEP}{args.amount:,}{Fmt.CURRENCY}'
        )
    else:
        print(f'{Prefix.ERROR} {Msg.Error.BUDGET_INVALID_CMD}')
        print(f'{Prefix.HINT} {Msg.Hint.BUDGET_INVALID_CMD}')
        return 1

    return 0


@handle_errors
def cmd_export(args: argparse.Namespace) -> int:
    if not args.month and not args.from_date and not args.to_date:
        print(f'{Prefix.ERROR} {Msg.Error.EXPORT_NO_FILTER}')
        print(f'{Prefix.HINT} {Msg.Hint.EXPORT_FILTER}')
        return 1

    svc   = BudgetService(args.data_dir)
    count = svc.export_transactions(args.out, args.month, args.from_date, args.to_date)
    if count == 0:
        print(f'{Prefix.INFO} {Msg.Info.NO_DATA}')
        return 0

    print(f'{Prefix.DONE.format(Prefix.SAVE)} {args.out} {Msg.Info.EXPORT_RESULT.format(count)}')
    return 0


@handle_errors
def cmd_import(args: argparse.Namespace) -> int:
    svc = BudgetService(args.data_dir)
    imported, skipped = svc.import_transactions(args.from_file)
    print(
        f'{Prefix.DONE.format(Prefix.SAVE)} '
        f'{Msg.Info.IMPORT_IMPORTED}{Fmt.KV_SEP}{imported}'
        f'{Fmt.LIST_SEP}{Msg.Info.IMPORT_SKIPPED}{Fmt.KV_SEP}{skipped}'
    )
    return 0


@handle_errors
def cmd_backup(args: argparse.Namespace) -> int:
    svc = BudgetService(args.data_dir)
    backup_dir = svc.backup()
    print(f'{Prefix.DONE.format(Prefix.BACKUP)} {Msg.Info.BACKUP_OK.format(backup_dir)}')
    return 0


@handle_errors
def cmd_category(args: argparse.Namespace) -> int:
    svc = BudgetService(args.data_dir)

    if args.category_cmd == CLI.Command.LIST:
        categories = svc.list_categories()
        print(f'{Prefix.CATEGORIES} ({len(categories)})')
        for i, c in enumerate(categories, 1):
            print(f'{i}. {c}')

    elif args.category_cmd == CLI.Command.ADD:
        category = _ask_new_category(svc.category_repo)
        svc.add_category(category)
        print(f'{Prefix.DONE.format(Prefix.SAVE)} {CLI.Command.CATEGORY}{Fmt.KV_SEP}{category}')

    elif args.category_cmd == CLI.Command.REMOVE:
        category = _ask_category(svc.category_repo)
        svc.remove_category(category)
        print(f'{Prefix.DONE.format(Prefix.REMOVE)} {CLI.Command.CATEGORY}{Fmt.KV_SEP}{category}')

    else:
        print(f'{Prefix.ERROR} {Msg.Error.CATEGORY_INVALID_CMD}')
        print(f'{Prefix.HINT} {Msg.Hint.CATEGORY_INVALID_CMD}')
        return 1

    return 0
