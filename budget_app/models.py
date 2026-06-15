from __future__ import annotations

from datetime import date
from dataclasses import dataclass, asdict

from .constants import TxType, TxField, RecurringField, Msg


@dataclass
class Transaction:
    id: str
    type: str       # income | expense
    date: str       # YYYY-MM-DD
    amount: int     # 양수
    category: str
    def __post_init__(self) -> None:
        if self.type not in TxType.ALL:
            raise ValueError(Msg.Error.TYPE_INVALID)
        try:
            date.fromisoformat(self.date)
        except (ValueError, TypeError):
            raise ValueError(Msg.Error.DATE_FORMAT)
        if not isinstance(self.amount, int) or self.amount <= 0:
            raise ValueError(Msg.Error.AMOUNT_NOT_POS)
        if not self.category:
            raise ValueError(Msg.Error.CATEGORY_EMPTY)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Transaction:
        return cls(**data)


@dataclass
class RecurringTx:
    id: str
    type: str    # income | expense
    day: int     # 1-31
    category: str
    amount: int

    def __post_init__(self) -> None:
        if self.type not in TxType.ALL:
            raise ValueError(Msg.Error.TYPE_INVALID)
        if not isinstance(self.day, int) or not (1 <= self.day <= 31):
            raise ValueError(Msg.Error.DAY_INVALID)
        if not isinstance(self.amount, int) or self.amount <= 0:
            raise ValueError(Msg.Error.AMOUNT_NOT_POS)
        if not self.category:
            raise ValueError(Msg.Error.CATEGORY_EMPTY)

    def to_dict(self) -> dict:
        return asdict(self)
