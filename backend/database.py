import os
from motor.motor_asyncio import AsyncIOMotorClient

client = None
db = None

def get_db():
    global client, db
    if client is None:
        mongo_uri = os.environ.get("MONGO_URI")
        if not mongo_uri:
            raise ValueError("MONGO_URI not set in environment")
        client = AsyncIOMotorClient(mongo_uri)
        db = client.pdf_edit_logbook
    return db

async def close_db():
    global client
    if client:
        client.close()
