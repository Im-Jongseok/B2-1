from __future__ import annotations

from datetime import date
from dataclasses import dataclass, asdict

from .constants import TxType, Msg


""" 거래 내역 데이터 모델"""
@dataclass
class Transaction:
    id: str
    type: str           # income || expense
    date: str           # YYYY-MM-DD
    amount: int         # 양수
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
    