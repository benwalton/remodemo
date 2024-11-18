import datetime

from pydantic import BaseModel

from models.db.transaction_model import TransactionType


class NewTransactionPayload(BaseModel):
    user_id: str
    amount: float
    currency: str
    timestamp: datetime.datetime
    type: TransactionType
