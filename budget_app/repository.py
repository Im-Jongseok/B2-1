from __future__ import annotations

import json
import os

from pathlib import Path
from typing import Generator

from .constants import DEFAULT_DATA_DIR, DEFAULT_CATEGORIES, Files, TxId, TxField
from .models import Transaction


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
        self._path = data_dir / Files.TRANSACTIONS
        create_jsonl(self._path)

    def stream(self) -> Generator[dict, None, None]:
        yield from read_jsonl(self._path)

    def generate_id(self) -> str:
        max_num = 0
        for record in self.stream():
            try:
                num  = int(record[TxField.ID].split(TxId.SEP)[1])
                if num > max_num:
                    max_num = num
            except (IndexError, ValueError):
                continue
        return TxId.FORMAT.format(max_num + 1)

    def add(self, transaction: Transaction) -> None:
        append_jsonl(self._path, transaction.to_dict())


""" 카테고리 저장소 """
class CategoryRepository:

    def __init__(self, data_dir: Path= DEFAULT_DATA_DIR) -> None:
        self._path = data_dir / Files.CATEGORIES
        create_jsonl(self._path)
        # (A) 기본 카태고리 자동 생성
        if self._is_empty():
            self._init_default()

    def _is_empty(self) -> bool:
        return os.path.getsize(self._path) == 0
    
    def _init_default(self) -> None:
        for category in DEFAULT_CATEGORIES:
            append_jsonl(self._path, {TxField.CATEGORY: category})

    def list_categories(self) -> list[str]:
        return [record[TxField.CATEGORY] for record in read_jsonl(self._path)]
    
    def exists(self, category: str) -> bool:
        return category in self.list_categories()