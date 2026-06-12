from __future__ import annotations

from datetime import date
from dataclasses import dataclass, asdict


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
    