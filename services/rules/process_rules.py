from typing import Optional, List

from motor.motor_asyncio import AsyncIOMotorDatabase

import config
from db import db
from models.db.transaction_model import TransactionType, SuspiciousReasonsType
from models.payloads.new_transaction_payload import NewTransactionPayload
from repositories.transaction_repository import TransactionRepository
from redis.asyncio import Redis

settings =config.get_settings()


FLAG_AMOUNT_THRESHOLD = 10000
FREQUENT_SMALL_TRANSACTIONS_PER_HOUR_MAX = 4
FREQUENT_SMALL_TRANSACTIONS_LIMIT = 100.00  # $100 classed as small transaction
RAPID_TRANSFERS_MINUTES = 5
RAPID_TRANSFER_MAX = 2


redis = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)


class ProcessRules:

    def __init__(
        self,
        transaction: NewTransactionPayload,
        database: Optional[AsyncIOMotorDatabase] = None,
    ):
        self.transaction = transaction
        self.db = database or db
        self.transaction_repo = TransactionRepository(db=self.db)

    async def __call__(self) -> List[str]:
        reasons = []
        high_volume = await self.is_high_volume()
        if high_volume:
            reasons.append(high_volume)

        frequent_small = await self.has_frequent_small_transactions()
        if frequent_small:
            reasons.append(frequent_small)

        rapid_transfers = await self.has_rapid_transfers()
        if rapid_transfers:
            reasons.append(rapid_transfers)

        return reasons

    async def is_high_volume(self):
        if self.transaction.amount > FLAG_AMOUNT_THRESHOLD:
            return SuspiciousReasonsType.HIGH_VOLUME_TRANSACTION

    async def has_frequent_small_transactions(self):
        # We use redis here to save constantly running the same query if there
        # are multiple transactions going on for a particular user.
        redis_key = f"small_transactions{self.transaction.user_id}"
        exists = await redis.get(redis_key)
        if exists:
            return SuspiciousReasonsType.FREQUENT_SMALL_TRANSACTIONS

        # If the current transaction is not a small transaction then we don't
        # check the previous transactions
        if self.transaction.amount <= FREQUENT_SMALL_TRANSACTIONS_LIMIT:
            transactions = await self.transaction_repo.get_recent_transactions_for_user(
                user_id=self.transaction.user_id,
                minutes=60,
                max_amount=FREQUENT_SMALL_TRANSACTIONS_LIMIT,
            )
            if len(transactions) >= FREQUENT_SMALL_TRANSACTIONS_PER_HOUR_MAX:
                # We have hit a frequent transaction limit, we can cache this in redis
                # to prevent running this query constantly

                # Technically we should set this to 1 hour from the first transaction
                # but for simplicity will mark all future small transactions as suspicious
                # for the next hour
                await redis.set(redis_key, 1, ex=3600)
                return SuspiciousReasonsType.FREQUENT_SMALL_TRANSACTIONS

    async def has_rapid_transfers(self):
        redis_key = f"rapid_transfers{self.transaction.user_id}"
        exists = await redis.get(redis_key)
        if exists:
            return SuspiciousReasonsType.RAPID_TRANSFERS

        # Ensure the current transaction is a transfer
        if self.transaction.type == TransactionType.TRANSFER:
            transactions = await self.transaction_repo.get_recent_transactions_for_user(
                user_id=self.transaction.user_id,
                minutes=RAPID_TRANSFERS_MINUTES,
                types=[TransactionType.TRANSFER],
            )
            # This becomes >= as the limit is e.g. 4. So 4 from the DB and 1 from the current one goes over the limit
            if len(transactions) >= RAPID_TRANSFER_MAX:
                # Store in Redis so we don't have to keep running this query.
                await redis.set(redis_key, 1, ex=300)  # 5mins
                return SuspiciousReasonsType.RAPID_TRANSFERS
