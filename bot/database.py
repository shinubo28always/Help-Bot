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
# Database object create kar liya
db = Database()
