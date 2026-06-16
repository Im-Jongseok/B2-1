from __future__ import annotations

import argparse
from itertools import islice
from typing import Callable, NamedTuple

from .constants import (
    TxType, TxField, TxId, BudgetField, RecurringField, SummaryKey,
    Prefix, Msg, Prompt, CLI,
    Confirm, Fmt, ColWidth,
)
from .decorators import handle_errors
from .formatter import ljust_display, print_tx, print_tx_header, print_recurring
from .service import BudgetService


def _error(msg: str, hint: str | None = None) -> None:
    print(f'{Prefix.ERROR} {msg}')
    if hint:
        print(f'{Prefix.HINT} {hint}')


# ── 대화형 입력 헬퍼 ─────────────────────────────────────────────

def _ask_date() -> str:
    from datetime import date as _date
    while True:
        raw = input(Prompt.DATE).strip()
        try:
            _date.fromisoformat(raw)
            return raw
        except ValueError:
            _error(Msg.Error.DATE_FORMAT, Msg.Hint.DATE_FORMAT)


def _ask_type() -> str:
    while True:
        raw = input(Prompt.TYPE).strip().lower()
        if raw in TxType.ALL:
            return raw
        _error(Msg.Error.TYPE_INVALID, Msg.Hint.TYPE_INVALID)


def _ask_new_category(categories: list[str]) -> str:
    while True:
        raw = input(Prompt.CATEGORY).strip().lower()
        if not raw:
            _error(Msg.Error.CATEGORY_EMPTY)
            continue
        if raw in categories:
            _error(Msg.Error.CATEGORY_ALREADY_EXIST.format(raw), Msg.Hint.CATEGORY_LIST)
            continue
        return raw


def _ask_category(categories: list[str]) -> str:
    while True:
        print(f'{Prefix.CATEGORIES} {Fmt.LIST_SEP.join(categories)}')
        raw = input(Prompt.CATEGORY).strip().lower()
        if raw in categories:
            return raw
        _error(Msg.Error.CATEGORY_NOT_FOUND.format(raw), Msg.Hint.CATEGORY_ADD)


def _ask_amount() -> int:
    while True:
        raw = input(Prompt.AMOUNT).strip()
        try:
            amount = int(raw)
            if amount <= 0:
                _error(Msg.Error.AMOUNT_NOT_POS, Msg.Hint.AMOUNT)
                continue
            return amount
        except ValueError:
            _error(Msg.Error.AMOUNT_NOT_NUM, Msg.Hint.AMOUNT)


def _ask_day() -> int:
    while True:
        raw = input(Prompt.DAY).strip()
        try:
            day = int(raw)
            if 1 <= day <= 31:
                return day
            _error(Msg.Error.DAY_INVALID, Msg.Hint.DAY)
        except ValueError:
            _error(Msg.Error.DAY_INVALID, Msg.Hint.DAY)


def _ask_fields(prompt: str, field_handlers: dict) -> dict:
    raw = input(prompt).strip().lower()
    tokens = raw.split()
    selected = [f for f in tokens if f in field_handlers]
    unknown  = [f for f in tokens if f not in field_handlers]
    if unknown:
        print(f'{Prefix.WARN} {Msg.Warn.UNKNOWN_FIELD.format(Fmt.LIST_SEP.join(unknown))}')
    return {field: field_handlers[field]() for field in selected}


def _ask_update_recurring_fields(categories: list[str]) -> dict:
    return _ask_fields(Prompt.UPDATE_RECURRING_FIELDS, {
        RecurringField.TYPE:     _ask_type,
        RecurringField.DAY:      _ask_day,
        RecurringField.CATEGORY: lambda: _ask_category(categories),
        RecurringField.AMOUNT:   _ask_amount,
    })


def _ask_update_fields(categories: list[str]) -> dict:
    return _ask_fields(Prompt.UPDATE_FIELDS, {
        TxField.DATE:     _ask_date,
        TxField.TYPE:     _ask_type,
        TxField.CATEGORY: lambda: _ask_category(categories),
        TxField.AMOUNT:   _ask_amount,
    })


def _input_tx(svc: BudgetService) -> dict:
    return {
        TxField.DATE:     _ask_date(),
        TxField.TYPE:     _ask_type(),
        TxField.CATEGORY: _ask_category(svc.list_categories()),
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
        _error(Msg.Error.NO_CHANGES)
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
        _error(Msg.Error.CONFIRM_INVALID, Msg.Hint.CONFIRM_INVALID)
        return 1
    delete_fn(id_val)
    print(f'{Prefix.DONE.format(Prefix.REMOVE)} {id_field}{Fmt.KV_SEP}{id_val}')
    return 0


class _Target(NamedTuple):
    record: dict | None
    print_fn: Callable
    id_field: str
    not_found: str
    hint: str
    ask: Callable
    update: Callable
    delete: Callable


def _resolve(svc: BudgetService, rec_id: str) -> _Target:
    """ID 접두사로 거래/반복 내역을 구분해 처리에 필요한 바인딩을 반환."""
    if rec_id.startswith(TxId.RX_PREFIX):
        return _Target(
            record=svc.find_recurring(rec_id),
            print_fn=print_recurring, id_field=RecurringField.ID,
            not_found=Msg.Error.RECURRING_NOT_FOUND, hint=Msg.Hint.RECURRING_ID,
            ask=lambda: _ask_update_recurring_fields(svc.list_categories()),
            update=svc.update_recurring, delete=svc.delete_recurring,
        )
    return _Target(
        record=svc.find_transaction(rec_id),
        print_fn=print_tx, id_field=TxField.ID,
        not_found=Msg.Error.TX_NOT_FOUND, hint=Msg.Hint.TX_ID,
        ask=lambda: _ask_update_fields(svc.list_categories()),
        update=svc.update_transaction, delete=svc.delete_transaction,
    )


# ── 커맨드 핸들러 ─────────────────────────────────────────────────

@handle_errors
def cmd_add(args: argparse.Namespace) -> int:
    svc = BudgetService(args.data_dir)
    if args.recurring:
        tx_type  = _ask_type()
        category = _ask_category(svc.list_categories())
        day      = _ask_day()
        amount   = _ask_amount()
        rx = svc.add_recurring(tx_type, day, category, amount)
        print_recurring(rx.to_dict())
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
        for r in islice(records, args.limit):
            print_recurring(r)
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
        msg += f', {Msg.Info.APPLY_SKIPPED.format(skipped)}'
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
    t = _resolve(svc, args.tx_id)
    if t.record is None:
        _error(t.not_found.format(args.tx_id), t.hint)
        return 1
    return _run_update(t.record, t.print_fn, t.ask, t.update, t.id_field, args.tx_id)


@handle_errors
def cmd_delete(args: argparse.Namespace) -> int:
    svc = BudgetService(args.data_dir)
    t = _resolve(svc, args.tx_id)
    if t.record is None:
        _error(t.not_found.format(args.tx_id), t.hint)
        return 1
    return _run_delete(t.record, t.print_fn, t.delete, t.id_field, args.tx_id)


@handle_errors
def cmd_summary(args: argparse.Namespace) -> int:
    svc  = BudgetService(args.data_dir)
    data = svc.get_summary(args.month, args.top)
    budget = data[SummaryKey.BUDGET]

    if (data[SummaryKey.INCOME_TOTAL] == 0
            and data[SummaryKey.EXPENSE_TOTAL] == 0
            and budget is None):
        print(f'{Prefix.INFO} {Msg.Info.NO_DATA}')
        return 0

    print(f'{Prefix.SUMMARY.format(args.month)}')
    print(f'{Msg.Info.INCOME_TOTAL}: {data[SummaryKey.INCOME_TOTAL]:,}{Fmt.CURRENCY}')
    print(f'{Msg.Info.EXPENSE_TOTAL}: {data[SummaryKey.EXPENSE_TOTAL]:,}{Fmt.CURRENCY}')
    print(f'{Msg.Info.BALANCE}: {data[SummaryKey.BALANCE]:,}{Fmt.CURRENCY}')

    if data[SummaryKey.TOP_EXPENSE]:
        print(f'\n{Prefix.TOP_EXPENSE.format(args.top)}')
        for i, (cat, amt) in enumerate(data[SummaryKey.TOP_EXPENSE], 1):
            print(f'{i}) {ljust_display(cat, ColWidth.CATEGORY)} {amt:,}{Fmt.CURRENCY}')

    if budget is not None and budget > 0:
        usage = data[SummaryKey.EXPENSE_TOTAL] / budget * Fmt.PERCENT_FACTOR
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
        _error(Msg.Error.BUDGET_INVALID_CMD, Msg.Hint.BUDGET_INVALID_CMD)
        return 1

    return 0


@handle_errors
def cmd_export(args: argparse.Namespace) -> int:
    if not args.month and not args.from_date and not args.to_date:
        _error(Msg.Error.EXPORT_NO_FILTER, Msg.Hint.EXPORT_FILTER)
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
        category = _ask_new_category(svc.list_categories())
        svc.add_category(category)
        print(f'{Prefix.DONE.format(Prefix.SAVE)} {CLI.Command.CATEGORY}{Fmt.KV_SEP}{category}')

    elif args.category_cmd == CLI.Command.REMOVE:
        category = _ask_category(svc.list_categories())
        svc.remove_category(category)
        print(f'{Prefix.DONE.format(Prefix.REMOVE)} {CLI.Command.CATEGORY}{Fmt.KV_SEP}{category}')

    else:
        _error(Msg.Error.CATEGORY_INVALID_CMD, Msg.Hint.CATEGORY_INVALID_CMD)
        return 1

    return 0
