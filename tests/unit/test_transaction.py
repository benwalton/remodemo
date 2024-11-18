import datetime
import unittest
from unittest import mock

from mongomock_motor import AsyncMongoMockClient

from models.db.transaction_model import (
    TransactionModel,
    TransactionType,
    SuspiciousReasonsType,
)
from models.payloads.new_transaction_payload import NewTransactionPayload
from services.transaction.new_transaction import NewTransaction


class TestTransaction(unittest.IsolatedAsyncioTestCase):


    @mock.patch("services.rules.process_rules.redis")
    async def test_new_transaction(self, _redis):
        # Ignore caching for now
        _redis.get.return_value = None

        db = AsyncMongoMockClient()["tests"]

        new_transaction_payload = NewTransactionPayload(
            user_id="user1234",
            amount="500",
            currency="USD",
            timestamp=datetime.datetime.utcnow(),
            type="DEPOSIT",
        )

        await NewTransaction(transaction=new_transaction_payload, database=db)()

        transaction_collection = db["transaction"]
        transaction = await transaction_collection.find_one()
        transaction_model = TransactionModel(**transaction)

        self.assertEqual(transaction_model.user_id, "user1234")
        self.assertEqual(transaction_model.amount, 500)
        self.assertEqual(transaction_model.currency, "USD"),
        self.assertEqual(transaction_model.type, TransactionType.DEPOSIT)
        self.assertEqual(transaction_model.is_suspicious, False)
        self.assertEqual(transaction_model.suspicious_reasons, [])

    @mock.patch("services.rules.process_rules.redis")
    async def test_new_transaction_above_high_value(self, _redis):
        _redis.get.return_value = None

        db = AsyncMongoMockClient()["tests"]

        new_transaction_payload = NewTransactionPayload(
            user_id="user1234",
            amount="10001",
            currency="USD",
            timestamp=datetime.datetime.utcnow(),
            type="DEPOSIT",
        )

        await NewTransaction(transaction=new_transaction_payload, database=db)()

        transaction_collection = db["transaction"]
        transaction = await transaction_collection.find_one()
        transaction_model = TransactionModel(**transaction)

        self.assertEqual(transaction_model.user_id, "user1234")
        self.assertEqual(transaction_model.amount, 10001)
        self.assertEqual(transaction_model.currency, "USD"),
        self.assertEqual(transaction_model.type, TransactionType.DEPOSIT)
        self.assertEqual(transaction_model.is_suspicious, True)
        self.assertEqual(
            transaction_model.suspicious_reasons,
            [SuspiciousReasonsType.HIGH_VOLUME_TRANSACTION],
        )

    @mock.patch("services.rules.process_rules.redis")
    async def test_new_transaction_under_high_value(self, _redis):
        _redis.get.return_value = None

        db = AsyncMongoMockClient()["tests"]

        new_transaction_payload = NewTransactionPayload(
            user_id="user1234",
            amount="10000",
            currency="USD",
            timestamp=datetime.datetime.utcnow(),
            type="DEPOSIT",
        )

        await NewTransaction(transaction=new_transaction_payload, database=db)()

        transaction_collection = db["transaction"]
        transaction = await transaction_collection.find_one()
        transaction_model = TransactionModel(**transaction)

        self.assertEqual(transaction_model.user_id, "user1234")
        self.assertEqual(transaction_model.amount, 10000)
        self.assertEqual(transaction_model.currency, "USD"),
        self.assertEqual(transaction_model.type, TransactionType.DEPOSIT)
        self.assertEqual(transaction_model.is_suspicious, False)
        self.assertEqual(transaction_model.suspicious_reasons, [])

    @mock.patch("services.rules.process_rules.redis")
    async def test_new_transaction_rapid_transfers(self, _redis):
        _redis.get.return_value = None

        db = AsyncMongoMockClient()["tests"]

        # Create dates to be used for the transactions
        now = datetime.datetime.utcnow()
        the_dates = []
        for i in range(3):
            the_dates.append(now - datetime.timedelta(seconds=20 * i))

        # Create 2 transaction, they should all pass
        for i in range(2):
            new_transaction_payload = NewTransactionPayload(
                user_id="user1234",
                amount="10000",
                currency="USD",
                timestamp=the_dates.pop(),
                type="TRANSFER",
            )
            new_trans = await NewTransaction(
                transaction=new_transaction_payload, database=db
            )()
            new_trans_model = TransactionModel(**new_trans)
            self.assertEqual(new_trans_model.is_suspicious, False)

        # 3rd one should be too much
        new_transaction_payload = NewTransactionPayload(
            user_id="user1234",
            amount="10000",
            currency="USD",
            timestamp=the_dates.pop(),
            type="TRANSFER",
        )
        new_trans = await NewTransaction(
            transaction=new_transaction_payload, database=db
        )()
        new_trans_model = TransactionModel(**new_trans)
        self.assertEqual(new_trans_model.is_suspicious, True)
        self.assertEqual(
            new_trans_model.suspicious_reasons, [SuspiciousReasonsType.RAPID_TRANSFERS]
        )

    @mock.patch("services.rules.process_rules.redis")
    async def test_new_transaction_frequent_small(self, _redis):
        _redis.get.return_value = None

        db = AsyncMongoMockClient()["tests"]

        now = datetime.datetime.utcnow()
        the_dates = []
        for i in range(5):
            the_dates.append(now - datetime.timedelta(minutes=10 * i))

        for i in range(4):
            new_transaction_payload = NewTransactionPayload(
                user_id="user1234",
                amount="50",
                currency="USD",
                timestamp=the_dates.pop(),
                type="WITHDRAWAL",
            )
            new_trans = await NewTransaction(
                transaction=new_transaction_payload, database=db
            )()
            new_trans_model = TransactionModel(**new_trans)
            self.assertEqual(new_trans_model.is_suspicious, False)

        # 5th one should be too many
        new_transaction_payload = NewTransactionPayload(
            user_id="user1234",
            amount="50",
            currency="USD",
            timestamp=the_dates.pop(),
            type="WITHDRAWAL",
        )
        new_trans = await NewTransaction(
            transaction=new_transaction_payload, database=db
        )()
        new_trans_model = TransactionModel(**new_trans)
        self.assertEqual(new_trans_model.is_suspicious, True)
        self.assertEqual(
            new_trans_model.suspicious_reasons,
            [SuspiciousReasonsType.FREQUENT_SMALL_TRANSACTIONS],
        )

    @mock.patch("services.rules.process_rules.redis")
    async def test_new_transaction_frequent_small_cache(self, _redis):
        # Return True from the redis query
        _redis.get.side_effect = [True, False] # Will return True for frequent small and False for rapid

        db = AsyncMongoMockClient()["tests"]

        new_transaction_payload = NewTransactionPayload(
            user_id="user1234",
            amount="50",
            currency="USD",
            timestamp=datetime.datetime.utcnow(),
            type="WITHDRAWAL",
        )
        new_trans = await NewTransaction(
            transaction=new_transaction_payload, database=db
        )()
        new_trans_model = TransactionModel(**new_trans)
        self.assertEqual(new_trans_model.is_suspicious, True)
        self.assertEqual(
            new_trans_model.suspicious_reasons,
            [SuspiciousReasonsType.FREQUENT_SMALL_TRANSACTIONS],
        )

    @mock.patch("services.rules.process_rules.redis")
    async def test_new_transaction_rapid_transactions_cache(self, _redis):
        _redis.get.side_effect = [False, True]  # Will return False for frequent small and True for rapid

        db = AsyncMongoMockClient()["tests"]

        new_transaction_payload = NewTransactionPayload(
            user_id="user1234",
            amount="50",
            currency="USD",
            timestamp=datetime.datetime.utcnow(),
            type="WITHDRAWAL",
        )
        new_trans = await NewTransaction(
            transaction=new_transaction_payload, database=db
        )()
        new_trans_model = TransactionModel(**new_trans)
        self.assertEqual(new_trans_model.is_suspicious, True)
        self.assertEqual(
            new_trans_model.suspicious_reasons,
            [SuspiciousReasonsType.RAPID_TRANSFERS],
        )
