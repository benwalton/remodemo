from pymongo import ASCENDING, DESCENDING

import config
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorDatabase

_settings = config.get_settings()

client = motor.motor_asyncio.AsyncIOMotorClient(
    host=f"{_settings.MONGO_CONNECTION_STRING}/{_settings.MONGO_DATABASE}",
    username=_settings.MONGO_USER,
    password=_settings.MONGO_PASSWORD,
)

db: AsyncIOMotorDatabase = client[_settings.MONGO_DATABASE]


async def ensure_indexes():
    await db.transactions.create_index(
        [("user_id", ASCENDING), ("timestamp", DESCENDING)], background=True
    )
    await db.transactions.create_index("is_suspicious", background=True)
    await db.transactions.create_index("type", background=True)
    await db.transactions.create_index("amount", background=True)


# Call the index creation function at the time of initialization
import asyncio

asyncio.run(ensure_indexes())
