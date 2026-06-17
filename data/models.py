"""Data model definitions used across the application."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Fund:
    """Represents a tracked fund."""
    id: Optional[int] = None
    code: str = ""
    name: str = ""
    fund_type: str = ""
    nav_yesterday: float = 0.0
    added_at: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "fund_type": self.fund_type,
            "nav_yesterday": self.nav_yesterday,
            "added_at": self.added_at,
        }

    @classmethod
    def from_row(cls, row: dict) -> "Fund":
        return cls(**row)


@dataclass
class Holding:
    """Represents a single stock holding within a fund."""
    id: Optional[int] = None
    fund_id: int = 0
    stock_code: str = ""
    stock_name: str = ""
    market: str = ""
    weight: float = 0.0
    updated_at: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "fund_id": self.fund_id,
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "market": self.market,
            "weight": self.weight,
            "updated_at": self.updated_at,
        }


@dataclass
class ValuationRecord:
    """A single valuation snapshot."""
    id: Optional[int] = None
    fund_id: int = 0
    estimated_nav: float = 0.0
    change_pct: float = 0.0
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "fund_id": self.fund_id,
            "estimated_nav": self.estimated_nav,
            "change_pct": self.change_pct,
            "created_at": self.created_at,
        }
