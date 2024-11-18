from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from db import db
from models.db.transaction_model import TransactionModel
from models.payloads.new_transaction_payload import NewTransactionPayload
from repositories.transaction_repository import TransactionRepository
from services.rules.process_rules import ProcessRules


class NewTransaction:
    def __init__(
        self,
        transaction: NewTransactionPayload,
        database: Optional[AsyncIOMotorDatabase] = None,
    ):
        self.transaction = transaction
        self.db = database or db
        self.transaction_repo = TransactionRepository(db=self.db)

    async def __call__(self) -> dict:
        suspicious_reasons = await ProcessRules(
            transaction=self.transaction, database=self.db
        )()
        transaction = await self.transaction_repo.insert_transaction(
            {
                **self.transaction.model_dump(),
                "is_suspicious": len(suspicious_reasons) != 0,
                "suspicious_reasons": suspicious_reasons,
            }
        )
        return transaction.to_dict_json()
