from __future__ import annotations

from pathlib import Path

from .constants import DEFAULT_DATA_DIR
from .models import Transaction
from .repository import TransactionRepository, CategoryRepository


""" 가계부 로직 """
class BudgetService:

    def __init__(self, data_dir: Path = DEFAULT_DATA_DIR):
        self.tx_repo = TransactionRepository(data_dir)
        self.category_repo = CategoryRepository(data_dir)

    def add_transaction(
            self,
            type: str,
            date: str,
            amount: int,
            category: str,
    ) -> Transaction:
        
        if not self.category_repo.exists(category):
            raise ValueError()
        
        tx_id = self.tx_repo.generate_id()
        tx = Transaction(
            id = tx_id,
            type=type,
            date=date,
            amount=amount,
            category=category
        )
        self.tx_repo.add(tx)
    
        return tx