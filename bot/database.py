from motor.motor_asyncio import AsyncIOMotorClient
from bot.config import Config

class Database:
    def __init__(self):
        self.client = AsyncIOMotorClient(Config.MONGO_URI)
        self.db = self.client["AnimeBotDB"]
        
        # Collections (Tables)
        self.users = self.db["users"]       # Owner/Admins ke liye
        self.channels = self.db["channels"] # Channel settings (Caption, Title) ke liye
        self.settings = self.db["settings"] # GC command (/l, /lx) save karne ke liye

    async def get_active_command(self):
        data = await self.settings.find_one({"_id": "leech_cmd"})
        return data["cmd"] if data else "/l" # Default /l rakha hai

    async def set_active_command(self, cmd):
        await self.settings.update_one({"_id": "leech_cmd"}, {"$set": {"cmd": cmd}}, upsert=True)

# Yeh channel data save karega jab aap /setcap use karenge
    async def set_channel_map(self, title: str, channel_id: int, caption: str):
        await self.channels.update_one(
            {"_id": title.lower()},
            {"$set": {"title": title, "channel_id": channel_id, "caption": caption}},
            upsert=True
        )

    # Yeh data nikalega jab file upload karni hogi
    async def get_channel_map(self, title: str):
        return await self.channels.find_one({"_id": title.lower()})

# === ADMIN MANAGEMENT ===
    async def add_admin(self, user_id: int):
        await self.users.update_one({"_id": user_id}, {"$set": {"is_admin": True}}, upsert=True)

    async def remove_admin(self, user_id: int):
        await self.users.delete_one({"_id": user_id})

    async def get_admins(self):
        cursor = self.users.find({"is_admin": True})
        return [doc["_id"] async for doc in cursor]

    async def is_admin(self, user_id: int):
        from bot.config import Config
        if user_id == Config.OWNER_ID:
            return True # Owner hamesha admin hota hai
        user = await self.users.find_one({"_id": user_id, "is_admin": True})
        return bool(user)
# Database object create kar liya
db = Database()
