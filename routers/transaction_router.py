from fastapi import APIRouter

from models.payloads.new_transaction_payload import NewTransactionPayload
from services.transaction.get_suspicious_transactions import GetSuspiciousTransactions
from services.transaction.new_transaction import NewTransaction


class TransactionRouter:

    @property
    def router(self) -> APIRouter:
        api_router = APIRouter()

        @api_router.post("/transactions")
        async def new_transaction(body: NewTransactionPayload):
            return await NewTransaction(transaction=body)()

        @api_router.get("/transactions/suspicious/{user_id}")
        async def fetch_suspicious_transactions(user_id: str):
            return await GetSuspiciousTransactions(user_id=user_id)()

        return api_router
