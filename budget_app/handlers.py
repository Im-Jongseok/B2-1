from __future__ import annotations

import argparse
import csv
import shutil

from collections import defaultdict
from datetime import date, datetime
from itertools import islice

from .constants import (
    TxType, TxField, BudgetField,
    Prefix, Msg, Prompt, CLI,
    Confirm, Fmt, ColWidth, Files,
)
from .decorators import handle_errors
from .formatter import ljust_display, print_tx, print_tx_header
from .models import Transaction
from .repository import TransactionRepository, CategoryRepository, BudgetRepository
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
    tokens = raw.split()
    selected = [f for f in tokens if f in FIELD_HANDLERS]
    unknown = [f for f in tokens if f not in FIELD_HANDLERS]
    if unknown:
        print(f'{Prefix.WARN} {Msg.Warn.UNKNOWN_FIELD.format(Fmt.LIST_SEP.join(unknown))}')
    return {field: FIELD_HANDLERS[field]() for field in selected}


def _input_tx(svc: BudgetService) -> dict:
    """add 명령에 필요한 필드를 순차적으로 입력받아 dict로 반환한다."""
    return {
        TxField.DATE:     _ask_date(),
        TxField.TYPE:     _ask_type(),
        TxField.CATEGORY: _ask_category(svc.category_repo),
        TxField.AMOUNT:   _ask_amount(),
    }



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

@handle_errors
def cmd_add(args: argparse.Namespace) -> int:
    service = BudgetService(args.data_dir)
    tx = _input_tx(service)
    result = service.add_transaction(**tx)
    print(f'{Prefix.DONE.format(Prefix.SAVE)} {Msg.Info.SAVE_OK.format(result.id)}')
    print(ColWidth.SEP_LINE)
    print_tx(result.to_dict())
    print(ColWidth.SEP_LINE)
    return 0


@handle_errors
def cmd_search(args: argparse.Namespace) -> int:
    tx_repo = TransactionRepository(args.data_dir)
    records = [
        r for r in tx_repo.stream()
        if _matches_filter(r, args.from_date, args.to_date, args.tx_type, args.category)
    ]
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
    tx_repo = TransactionRepository(args.data_dir)

    record = tx_repo.find(args.tx_id)
    if record is None:
        print(f'{Prefix.ERROR} {Msg.Error.TX_NOT_FOUND.format(args.tx_id)}')
        print(f'{Prefix.HINT} {Msg.Hint.TX_ID}')
        return 1

    print(f'{Msg.Info.BEFORE}')
    print(ColWidth.SEP_LINE)
    print_tx(record)
    print(ColWidth.SEP_LINE)

    category_repo = CategoryRepository(args.data_dir)
    fields = _ask_update_fields(category_repo)

    if not fields:
        print(f'{Prefix.ERROR} {Msg.Error.NO_CHANGES}')
        return 1

    tx_repo.update(args.tx_id, fields)
    print(f'{Prefix.DONE.format(Prefix.SAVE)} {TxField.ID}{Fmt.KV_SEP}{args.tx_id}')
    print(f'{Msg.Info.AFTER}')
    print(ColWidth.SEP_LINE)
    print_tx({**record, **fields})
    print(ColWidth.SEP_LINE)
    return 0


@handle_errors
def cmd_delete(args: argparse.Namespace) -> int:
    tx_repo = TransactionRepository(args.data_dir)

    record = tx_repo.find(args.tx_id)
    if record is None:
        print(f'{Prefix.ERROR} {Msg.Error.TX_NOT_FOUND.format(args.tx_id)}')
        print(f'{Prefix.HINT} {Msg.Hint.TX_ID}')
        return 1

    print_tx(record)
    confirm = input(Prompt.DELETE_CONFIRM).strip().lower()
    if confirm == Confirm.NO:
        print(f'{Prefix.INFO} {Msg.Info.DELETE_CANCELLED}')
        return 0
    elif confirm != Confirm.YES:
        print(f'{Prefix.ERROR} {Msg.Error.CONFIRM_INVALID}')
        print(f'{Prefix.HINT} {Msg.Hint.CONFIRM_INVALID}')
        return 1


    tx_repo.delete(args.tx_id)
    print(f'{Prefix.DONE.format(Prefix.REMOVE)} {TxField.ID}{Fmt.KV_SEP}{args.tx_id}')
    return 0


@handle_errors
def cmd_summary(args: argparse.Namespace) -> int:
    tx_repo = TransactionRepository(args.data_dir)
    budget_repo = BudgetRepository(args.data_dir)

    income_total = 0
    expense_total = 0
    category_expense: dict = defaultdict(int)

    for r in tx_repo.stream():
        if not r[TxField.DATE].startswith(args.month):
            continue
        if r[TxField.TYPE] == TxType.INCOME:
            income_total += r[TxField.AMOUNT]
        else:
            expense_total += r[TxField.AMOUNT]
            category_expense[r[TxField.CATEGORY]] += r[TxField.AMOUNT]

    if income_total == 0 and expense_total == 0:
        print(f'{Prefix.INFO} {Msg.Info.NO_DATA}')
        return 0

    print(f'{Prefix.SUMMARY.format(args.month)}')
    print(f'{Msg.Info.INCOME_TOTAL}: {income_total:,}{Fmt.CURRENCY}')
    print(f'{Msg.Info.EXPENSE_TOTAL}: {expense_total:,}{Fmt.CURRENCY}')
    print(f'{Msg.Info.BALANCE}: {income_total - expense_total:,}{Fmt.CURRENCY}')

    if category_expense:
        top = sorted(category_expense.items(), key=lambda x: x[1], reverse=True)[:args.top]
        print(f'\n{Prefix.TOP_EXPENSE.format(args.top)}')
        for i, (cat, amt) in enumerate(top, 1):
            print(f'{i}) {ljust_display(cat, 12)} {amt:,}{Fmt.CURRENCY}')

    budget = budget_repo.get(args.month)
    if budget is not None:
        usage = expense_total / budget * 100
        print(f'\n{Prefix.BUDGET_SECTION}')
        print(f'{Msg.Info.BUDGET_AMOUNT}: {budget:,}{Fmt.CURRENCY}')
        print(f'{Msg.Info.BUDGET_USAGE}: {expense_total:,}{Fmt.CURRENCY} ({usage:.1f}{Fmt.PERCENT})')
        if expense_total > budget:
            over = expense_total - budget
            print(f'{Prefix.WARN} {Msg.Warn.BUDGET_EXCEEDED.format(f"{over:,}")}')

    return 0


@handle_errors
def cmd_budget(args: argparse.Namespace) -> int:
    budget_repo = BudgetRepository(args.data_dir)

    if args.budget_cmd == CLI.Command.SET:
        if args.amount <= 0:
            print(f'{Prefix.ERROR} {Msg.Error.AMOUNT_NOT_POS}')
            print(f'{Prefix.HINT} {Msg.Hint.AMOUNT}')
            return 1
        budget_repo.set(args.month, args.amount)
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

    tx_repo = TransactionRepository(args.data_dir)
    results = tx_repo.stream()
    if args.month:
        results = (r for r in results if r[TxField.DATE].startswith(args.month))
    if args.from_date:
        results = (r for r in results if r[TxField.DATE] >= args.from_date)
    if args.to_date:
        results = (r for r in results if r[TxField.DATE] <= args.to_date)
    records = list(results)

    if not records:
        print(f'{Prefix.INFO} {Msg.Info.NO_DATA}')
        return 0

    fields = [TxField.ID, TxField.DATE, TxField.TYPE, TxField.AMOUNT, TxField.CATEGORY]
    with open(args.out, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)

    print(f'{Prefix.DONE.format(Prefix.SAVE)} {args.out} {Msg.Info.EXPORT_RESULT.format(len(records))}')
    return 0



@handle_errors
def cmd_import(args: argparse.Namespace) -> int:
    tx_repo = TransactionRepository(args.data_dir)
    category_repo = CategoryRepository(args.data_dir)
    existing_ids = {r[TxField.ID] for r in tx_repo.stream()}
    imported = 0
    skipped = 0

    with open(args.from_file, 'r', newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            try:
                if row[TxField.CATEGORY] not in category_repo.list_categories():
                    skipped += 1
                    continue
                tx = Transaction(
                    id=row[TxField.ID],
                    date=row[TxField.DATE],
                    type=row[TxField.TYPE],
                    amount=int(row[TxField.AMOUNT]),
                    category=row[TxField.CATEGORY],
                )
            except (ValueError, KeyError):
                skipped += 1
                continue

            if tx.id in existing_ids:
                skipped += 1
                continue

            tx_repo.add(tx)
            existing_ids.add(tx.id)
            imported += 1

    print(f'{Prefix.DONE.format(Prefix.SAVE)} {Msg.Info.IMPORT_IMPORTED}{Fmt.KV_SEP}{imported}{Fmt.LIST_SEP}{Msg.Info.IMPORT_SKIPPED}{Fmt.KV_SEP}{skipped}')
    return 0


@handle_errors
def cmd_backup(args: argparse.Namespace) -> int:
    timestamp  = datetime.now().strftime(Files.BACKUP_TS_FMT)
    backup_dir = args.data_dir / Files.BACKUP_DIR / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)

    for filename in [Files.TRANSACTIONS, Files.CATEGORIES, Files.BUDGETS]:
        src = args.data_dir / filename
        if src.exists():
            shutil.copy2(src, backup_dir / filename)

    print(f'{Prefix.DONE.format(Prefix.BACKUP)} {Msg.Info.BACKUP_OK.format(backup_dir)}')
    return 0


@handle_errors
def cmd_list(args: argparse.Namespace) -> int:
    tx_repo = TransactionRepository(args.data_dir)
    records = list(tx_repo.stream())
    if not records:
        print(f'{Prefix.INFO} {Msg.Info.NO_DATA}')
        return 0
    print(f'{Prefix.INFO} {Msg.Info.COUNT.format(len(records))}')
    print_tx_header()
    for record in islice(reversed(records), args.limit):
        print_tx(record)
    return 0


@handle_errors
def cmd_category(args: argparse.Namespace) -> int:
    category_repo = CategoryRepository(args.data_dir)

    if args.category_cmd == CLI.Command.LIST:
        categories = category_repo.list_categories()
        print(f'{Prefix.CATEGORIES} ({len(categories)})')
        for i, c in enumerate(categories, 1):
            print(f'{i}. {c}')

    elif args.category_cmd == CLI.Command.ADD:
        category = _ask_new_category(category_repo)
        category_repo.add(category)
        print(f'{Prefix.DONE.format(Prefix.SAVE)} {CLI.Command.CATEGORY}{Fmt.KV_SEP}{category}')
    
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
        print(f'{Prefix.DONE.format(Prefix.REMOVE)} {CLI.Command.CATEGORY}{Fmt.KV_SEP}{category}')
    
    else:
        print(f'{Prefix.ERROR} {Msg.Error.CATEGORY_INVALID_CMD}')
        print(f'{Prefix.HINT} {Msg.Hint.CATEGORY_INVALID_CMD}')
        return 1

    return 0 
