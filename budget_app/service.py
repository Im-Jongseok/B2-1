from __future__ import annotations

import calendar
import csv
import shutil

from datetime import datetime
from pathlib import Path

from .constants import (
    DEFAULT_DATA_DIR, Files, Msg, TxField, TxType, RecurringField, SummaryKey,
)
from .models import Transaction, RecurringTx
from .repository import (
    TransactionRepository, CategoryRepository, BudgetRepository, RecurringRepository,
)


class BudgetService:

    def __init__(self, data_dir: Path = DEFAULT_DATA_DIR) -> None:
        self.data_dir      = data_dir
        self.tx_repo       = TransactionRepository(data_dir)
        self.category_repo = CategoryRepository(data_dir)
        self.budget_repo   = BudgetRepository(data_dir)
        self.rx_repo       = RecurringRepository(data_dir)

    # ── 거래 ──────────────────────────────────────────────────────────

    def add_transaction(self, type: str, date: str, amount: int, category: str) -> Transaction:
        if not self.category_repo.exists(category):
            raise ValueError(Msg.Error.CATEGORY_NOT_FOUND.format(category))
        tx = Transaction(
            id=self.tx_repo.generate_id(),
            type=type, date=date, amount=amount, category=category,
        )
        self.tx_repo.add(tx)
        return tx

    def list_transactions(self) -> list[dict]:
        return list(self.tx_repo.stream())

    def find_transaction(self, tx_id: str) -> dict | None:
        return self.tx_repo.find(tx_id)

    def update_transaction(self, tx_id: str, fields: dict) -> None:
        record = self.tx_repo.find(tx_id)
        if record:
            Transaction(**{**record, **fields})  # 병합 결과를 모델로 검증
        self.tx_repo.update(tx_id, fields)

    def delete_transaction(self, tx_id: str) -> None:
        self.tx_repo.remove(tx_id)

    def search_transactions(
        self,
        from_date: str | None = None,
        to_date: str | None = None,
        tx_type: str | None = None,
        category: str | None = None,
    ) -> list[dict]:
        return [r for r in self.tx_repo.stream() if _matches_filter(r, from_date, to_date, tx_type, category)]

    # ── 반복 내역 ──────────────────────────────────────────────────────

    def add_recurring(self, type: str, day: int, category: str, amount: int) -> RecurringTx:
        rx = RecurringTx(
            id=self.rx_repo.generate_id(),
            type=type, day=day, category=category, amount=amount,
        )
        self.rx_repo.add(rx)
        return rx

    def list_recurring(self) -> list[dict]:
        return list(self.rx_repo.stream())

    def find_recurring(self, rx_id: str) -> dict | None:
        return self.rx_repo.find(rx_id)

    def update_recurring(self, rx_id: str, fields: dict) -> None:
        record = self.rx_repo.find(rx_id)
        if record:
            RecurringTx(**{**record, **fields})  # 병합 결과를 모델로 검증
        self.rx_repo.update(rx_id, fields)

    def delete_recurring(self, rx_id: str) -> None:
        self.rx_repo.remove(rx_id)

    def apply_recurring(self, month: str) -> tuple[int, int]:
        _validate_month(month)
        year, month_num = int(month[:4]), int(month[5:])
        last_day = calendar.monthrange(year, month_num)[1]

        existing = {
            (r[TxField.DATE], r[TxField.TYPE], r[TxField.CATEGORY], r[TxField.AMOUNT])
            for r in self.tx_repo.stream()
            if r[TxField.DATE].startswith(month)
        }

        created = skipped = 0
        for tmpl in self.rx_repo.stream():
            actual_day = min(tmpl[RecurringField.DAY], last_day)
            key = (
                f'{month}-{actual_day:02d}',
                tmpl[RecurringField.TYPE],
                tmpl[RecurringField.CATEGORY],
                tmpl[RecurringField.AMOUNT],
            )
            if key in existing:
                skipped += 1
                continue
            tx = Transaction(
                id=self.tx_repo.generate_id(),
                type=tmpl[RecurringField.TYPE],
                date=key[0],
                amount=tmpl[RecurringField.AMOUNT],
                category=tmpl[RecurringField.CATEGORY],
            )
            self.tx_repo.add(tx)
            existing.add(key)
            created += 1

        return created, skipped

    # ── 카테고리 ──────────────────────────────────────────────────────

    def list_categories(self) -> list[str]:
        return self.category_repo.list_categories()

    def add_category(self, category: str) -> None:
        if self.category_repo.exists(category):
            raise ValueError(Msg.Error.CATEGORY_ALREADY_EXIST.format(category))
        self.category_repo.add(category)

    def remove_category(self, category: str) -> None:
        if any(r[TxField.CATEGORY] == category for r in self.tx_repo.stream()):
            raise ValueError(Msg.Error.CATEGORY_USED.format(category))
        self.category_repo.remove(category)

    # ── 예산 ──────────────────────────────────────────────────────────

    def get_budget(self, month: str) -> int | None:
        return self.budget_repo.get(month)

    def set_budget(self, month: str, amount: int) -> None:
        _validate_month(month)
        if amount <= 0:
            raise ValueError(Msg.Error.AMOUNT_NOT_POS)
        self.budget_repo.set(month, amount)

    # ── 요약 ──────────────────────────────────────────────────────────

    def get_summary(self, month: str, top: int) -> dict:
        _validate_month(month)
        income_total = 0
        expense_total = 0
        category_expense: dict[str, int] = {}

        for r in self.tx_repo.stream():
            if not r[TxField.DATE].startswith(month):
                continue
            if r[TxField.TYPE] == TxType.INCOME:
                income_total += r[TxField.AMOUNT]
            else:
                expense_total += r[TxField.AMOUNT]
                cat = r[TxField.CATEGORY]
                category_expense[cat] = category_expense.get(cat, 0) + r[TxField.AMOUNT]

        return {
            SummaryKey.INCOME_TOTAL:  income_total,
            SummaryKey.EXPENSE_TOTAL: expense_total,
            SummaryKey.BALANCE:       income_total - expense_total,
            SummaryKey.TOP_EXPENSE:   sorted(category_expense.items(), key=lambda x: x[1], reverse=True)[:top],
            SummaryKey.BUDGET:        self.budget_repo.get(month),
        }

    # ── export / import / backup ──────────────────────────────────────

    def export_transactions(
        self,
        out: str | Path,
        month: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> int:
        if month:
            _validate_month(month)
        stream = self.tx_repo.stream()
        if month:
            stream = (r for r in stream if r[TxField.DATE].startswith(month))
        if from_date:
            stream = (r for r in stream if r[TxField.DATE] >= from_date)
        if to_date:
            stream = (r for r in stream if r[TxField.DATE] <= to_date)
        records = list(stream)

        if not records:
            return 0

        fields = [TxField.ID, TxField.DATE, TxField.TYPE, TxField.AMOUNT, TxField.CATEGORY]
        with open(out, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(records)

        return len(records)

    def import_transactions(self, from_file: str | Path) -> tuple[int, int]:
        existing_ids = {r[TxField.ID] for r in self.tx_repo.stream()}
        categories = set(self.category_repo.list_categories())
        imported = skipped = 0

        with open(from_file, 'r', newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                try:
                    if row[TxField.CATEGORY] not in categories:
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

                self.tx_repo.add(tx)
                existing_ids.add(tx.id)
                imported += 1

        return imported, skipped

    def backup(self) -> Path:
        timestamp  = datetime.now().strftime(Files.BACKUP_TS_FMT)
        backup_dir = self.data_dir / Files.BACKUP_DIR / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)

        for filename in [Files.TRANSACTIONS, Files.CATEGORIES, Files.BUDGETS, Files.RECURRING]:
            src = self.data_dir / filename
            if src.exists():
                shutil.copy2(src, backup_dir / filename)

        return backup_dir


def _validate_month(month: str) -> None:
    valid = len(month) == 7
    if valid:
        try:
            datetime.strptime(month, '%Y-%m')
        except ValueError:
            valid = False
    if not valid:
        raise ValueError(Msg.Error.MONTH_FORMAT.format(month))


def _matches_filter(
    r: dict,
    from_date: str | None,
    to_date: str | None,
    tx_type: str | None,
    category: str | None,
) -> bool:
    if from_date and r[TxField.DATE] < from_date:
        return False
    if to_date and r[TxField.DATE] > to_date:
        return False
    if tx_type and r[TxField.TYPE] != tx_type:
        return False
    if category and r[TxField.CATEGORY] != category:
        return False
    return True
