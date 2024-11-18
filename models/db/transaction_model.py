import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, Field

from models.types.py_object_id import PyObjectId


class TransactionType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER = "TRANSFER"
    OTHER = "OTHER"


class SuspiciousReasonsType(str, Enum):
    HIGH_VOLUME_TRANSACTION = "HIGH_VOLUME_TRANSACTION"
    FREQUENT_SMALL_TRANSACTIONS = "FREQUENT_SMALL_TRANSACTIONS"
    RAPID_TRANSFERS = "RAPID_TRANSFERS"


class TransactionModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    amount: float
    currency: str
    timestamp: datetime.datetime
    type: TransactionType
    is_suspicious: bool
    suspicious_reasons: List[SuspiciousReasonsType]

    def to_dict_json(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "amount": self.amount,
            "currency": self.currency,
            "timestamp": self.timestamp,
            "type": self.type.value,
            "is_suspicious": self.is_suspicious,
            "suspicious_reasons": [r.value for r in self.suspicious_reasons],
        }
