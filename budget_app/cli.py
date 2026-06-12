from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path
from typing import Generator

import argparse
import json
import os

DEFAULT_DATA_DIR = Path("../data")
DEFAULT_CATEGORIES = {
    'food',
    'shopping',
}



""" 거래 내역 데이터 모델"""
@dataclass
class Transaction:
    id: str
    type: str           # income || expense
    date: str           # YYYY-MM-DD
    amount: int         # 양수
    category: str

    def __post_init__(self) -> None:
        if self.type not in ('income', 'expense'):
            raise ValueError()
        
        try:
            date.fromisoformat(self.date)
        except (ValueError, TypeError):
            raise ValueError()
        
        if not isinstance(self.amount, int) or self.amount <= 0:
            raise ValueError()
        
        if not self.category:
            raise ValueError()
        
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> Transaction:
        return cls(**data)
    

""" JSONL """
def create_jsonl(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.touch()

def append_jsonl(path: Path, record: dict) -> None:
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def read_jsonl(path: Path) -> Generator[dict, None, None]:
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


""" 거래 내역 저장소"""
class TransactionRepository:

    def __init__(self, data_dir: Path = DEFAULT_DATA_DIR) -> None:
        self._path = data_dir / "transactions.jsonl"
        create_jsonl(self._path)

    def stream(self) -> Generator[dict, None, None]:
        yield from read_jsonl(self._path)

    def generate_id(self) -> str:
        max_num = 0
        for record in self.stream():
            try:
                num  = int(record['id'].split('-')[1])
                if num > max_num:
                    max_num = num
            except (IndexError, ValueError):
                continue
        return f"TX-{max_num + 1:06d}"

    def add(self, transaction: Transaction) -> None:
        append_jsonl(self._path, transaction.to_dict())


""" 카테고리 저장소 """
class CategoryRepository:

    def __init__(self, data_dir: Path= DEFAULT_DATA_DIR) -> None:
        self._path = data_dir / "categories.jsonl"
        create_jsonl(self._path)
        # (A) 기본 카태고리 자동 생성
        if self._is_empty():
            self._init_default()

    def _is_empty(self) -> bool:
        return os.path.getsize(self._path) == 0
    
    def _init_default(self) -> None:
        for category in DEFAULT_CATEGORIES:
            append_jsonl(self._path, {'category': category})

    def list_categories(self) -> list[str]:
        return [record['category'] for record in read_jsonl(self._path)]
    
    def exists(self, category: str) -> bool:
        return category in self.list_categories()
    
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


""" parser 구축 """
def _build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', type=Path, default=DEFAULT_DATA_DIR)

    sub = parser.add_subparsers(dest='command', help='사용가능한 명령어')
    sub.add_parser('add', help='거래 추가')

    return parser

""" 사용자 입력 """
def _input_tx(svc: BudgetService) -> dict:
    tx_date = _ask_date()
    tx_type = _ask_type()
    tx_category = _ask_category(svc)
    tx_amount = _ask_amount()

    return {'date': tx_date, 'type': tx_type, 'category': tx_category, 'amount': tx_amount}
        
def _ask_date() -> str:
    while True:
        raw = input("날짜(YYYY-MM-DD): ").strip()
        try:
            date.fromisoformat(raw)
            return raw
        except ValueError:
            print()

def _ask_type() -> str:
    while True:
        raw = input("타입(income/expense): ").strip().lower()
        if raw in ("income", "expense"):
            return raw


def _ask_category(svc: BudgetService) -> str:
    categories = svc.category_repo.list_categories()
    while True:
        print(f"[등록된 카테고리] {', '.join(categories)}")
        raw = input("카테고리: ").strip().lower()
        if not raw:
            continue
        if raw not in categories:
            continue
        return raw


def _ask_amount() -> int:
    while True:
        raw = input("금액(양수): ").strip()
        try:
            amount = int(raw)
            if amount <= 0:
                continue
            return amount
        except ValueError:
            print()


""" 거레 추가 """
def cmd_add(args: argparse.Namespace) -> int:

    service = BudgetService(args.data_dir)

    tx = _input_tx(service)
    service.add_transaction(**tx)

    return 0

_COMMANDS = {
    'add': cmd_add,
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