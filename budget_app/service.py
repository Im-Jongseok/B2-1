from __future__ import annotations

from pathlib import Path

from .constants import DEFAULT_DATA_DIR
from .models import Transaction
from .repository import TransactionRepository, CategoryRepository


class BudgetService:
    """거래·카테고리·예산에 대한 비즈니스 로직을 제공한다."""

    def __init__(self, data_dir: Path = DEFAULT_DATA_DIR) -> None:
        self.tx_repo = TransactionRepository(data_dir)
        self.category_repo = CategoryRepository(data_dir)

    def add_transaction(
        self,
        type: str,
        date: str,
        amount: int,
        category: str,
    ) -> Transaction:
        """카테고리 존재 여부를 확인한 뒤 거래를 저장하고 반환한다."""
        if not self.category_repo.exists(category):
            raise ValueError()

        tx_id = self.tx_repo.generate_id()
        tx = Transaction(
            id=tx_id,
            type=type,
            date=date,
            amount=amount,
            category=category,
        )
        self.tx_repo.add(tx)
        return tx
