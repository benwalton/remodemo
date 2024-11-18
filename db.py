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
