import datetime
from typing import List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection

from models.db.transaction_model import TransactionModel, TransactionType
from models.types.py_object_id import PyObjectId


class TransactionRepository:

    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db
        self._collection: AsyncIOMotorCollection = db["transaction"]

    async def get_transaction(self, id: PyObjectId) -> TransactionModel:
        transaction = await self._collection.find_one({"_id": id})
        if transaction:
            return TransactionModel(**transaction)

    async def insert_transaction(self, transaction: dict) -> TransactionModel:
        inserted_transaction = await self._collection.insert_one(transaction)
        return await self.get_transaction(inserted_transaction.inserted_id)

    async def get_recent_transactions_for_user(
        self,
        user_id: str,
        minutes=60,
        types=Optional[List[TransactionType]],
        max_amount=Optional[float],
    ) -> List[TransactionModel]:
        now = datetime.datetime.utcnow()
        past = now - datetime.timedelta(minutes=minutes)
        query = {"user_id": user_id, "timestamp": {"$gte": past}}
        if type(types) == list:
            query["type"] = {"$in": types}
        if type(max_amount) == float:
            query["amount"] = {"$lte": max_amount}
        return await self._collection.find(query).to_list(None)

    async def get_suspicious_transactions_for_user(
        self, user_id: str
    ) -> List[TransactionModel]:
        transactions = (
            await self._collection.find({"user_id": user_id, "is_suspicious": True})
            .sort("timestamp")
            .to_list(None)
        )
        return [TransactionModel(**t) for t in transactions]
