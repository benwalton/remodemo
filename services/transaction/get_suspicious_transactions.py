from typing import Optional, List

from motor.motor_asyncio import AsyncIOMotorDatabase

from db import db
from models.db.transaction_model import TransactionModel
from repositories.transaction_repository import TransactionRepository


class GetSuspiciousTransactions:

    def __init__(self, user_id: str, database: Optional[AsyncIOMotorDatabase] = None):
        self.user_id = user_id
        self.db = database or db
        self.transaction_repo = TransactionRepository(db=self.db)

    async def __call__(self) -> List[dict]:
        transactions = await self.transaction_repo.get_suspicious_transactions_for_user(
            user_id=self.user_id
        )
        return [t.to_dict_json() for t in transactions]
