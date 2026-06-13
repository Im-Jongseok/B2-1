from __future__ import annotations

import json
import os
import tempfile

from pathlib import Path
from typing import Generator

from .constants import DEFAULT_DATA_DIR, DEFAULT_CATEGORIES, Files, TxId, TxField
from .models import Transaction


# ── JSONL 헬퍼 ───────────────────────────────────────────────

def create_jsonl(path: Path) -> None:
    """파일이 없으면 빈 JSONL 파일을 생성한다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.touch()


def append_jsonl(path: Path, record: dict) -> None:
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> Generator[dict, None, None]:
    """파일을 한 줄씩 스트리밍으로 읽는다. 메모리에 전체를 올리지 않는다."""
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

# atomic write
def rewrite_jsonl(path: Path, records: list[dict]) -> None:
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            dir=path.parent,
            suffix='.tmp',
            encoding='utf-8',
            delete=False,
        ) as fd:
            tmp_path = fd.name
            for record in records:
                fd.write(json.dumps(record, ensure_ascii=False) + '\n')
            fd.flush()
            os.fsync(fd.fileno())
        os.replace(tmp_path, path)
    except Exception:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise



# ── 저장소 ───────────────────────────────────────────────────

class TransactionRepository:
    """거래 내역의 JSONL 파일 I/O를 담당한다."""

    def __init__(self, data_dir: Path = DEFAULT_DATA_DIR) -> None:
        self._path = data_dir / Files.TRANSACTIONS
        create_jsonl(self._path)

    def stream(self) -> Generator[dict, None, None]:
        """저장된 거래를 오래된 순서로 스트리밍한다."""
        yield from read_jsonl(self._path)

    def generate_id(self) -> str:
        """현재 최대 ID 번호를 기준으로 다음 ID를 생성한다."""
        max_num = 0
        for record in self.stream():
            try:
                num = int(record[TxField.ID].split(TxId.SEP)[1])
                if num > max_num:
                    max_num = num
            except (IndexError, ValueError):
                continue
        return TxId.FORMAT.format(max_num + 1)

    def add(self, transaction: Transaction) -> None:
        append_jsonl(self._path, transaction.to_dict())


class CategoryRepository:
    """카테고리 목록의 JSONL 파일 I/O를 담당한다."""

    def __init__(self, data_dir: Path = DEFAULT_DATA_DIR) -> None:
        self._path = data_dir / Files.CATEGORIES
        create_jsonl(self._path)
        # 파일이 비어있으면 기본 카테고리를 자동으로 채운다 (안 A)
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

    def add(self, category: str) -> None:
        append_jsonl(self._path, {TxField.CATEGORY: category})
    
    def remove(self, category: str) -> bool:
        records = list(read_jsonl(self._path))
        # atomic delete
        new_records = [r for r in records if r[TxField.CATEGORY] != category]

        rewrite_jsonl(self._path, new_records)
        return True
