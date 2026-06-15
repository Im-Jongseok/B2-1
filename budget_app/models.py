from __future__ import annotations

from datetime import date as _date
from dataclasses import dataclass, asdict

from .constants import TxType, Msg


def _validate_type(type: str) -> None:
    if type not in TxType.ALL:
        raise ValueError(Msg.Error.TYPE_INVALID)


def _validate_amount(amount: int) -> None:
    if isinstance(amount, bool) or not isinstance(amount, int):
        raise ValueError(Msg.Error.AMOUNT_NOT_NUM)
    if amount <= 0:
        raise ValueError(Msg.Error.AMOUNT_NOT_POS)


def _validate_category(category: str) -> None:
    if not category:
        raise ValueError(Msg.Error.CATEGORY_EMPTY)


@dataclass
class Transaction:
    id: str
    type: str       # income | expense
    date: str       # YYYY-MM-DD
    amount: int     # 양수
    category: str

    def __post_init__(self) -> None:
        _validate_type(self.type)
        _validate_amount(self.amount)
        _validate_category(self.category)
        try:
            _date.fromisoformat(self.date)
        except (ValueError, TypeError):
            raise ValueError(Msg.Error.DATE_FORMAT)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RecurringTx:
    id: str
    type: str    # income | expense
    day: int     # 1-31
    category: str
    amount: int

    def __post_init__(self) -> None:
        _validate_type(self.type)
        _validate_amount(self.amount)
        _validate_category(self.category)
        if isinstance(self.day, bool) or not isinstance(self.day, int):
            raise ValueError(Msg.Error.DAY_INVALID)
        if not (1 <= self.day <= 31):
            raise ValueError(Msg.Error.DAY_INVALID)

    def to_dict(self) -> dict:
        return asdict(self)
