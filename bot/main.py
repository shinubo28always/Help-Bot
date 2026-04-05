import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from bot.config import Config
from bot.database import db

# Pyrogram Client Setup
app = Client(
    "AnimeUploaderBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="bot") # YEH LINE ADD KARNI HAI (Taake gc_handler automatically connect ho jaye)
)

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    if message.from_user.id != Config.OWNER_ID:
        return await message.reply_text("Bhai, yeh ek private bot hai. Aap isay use nahi kar sakte.")
    
    await message.reply_text(
        f"Hello Master! Main zinda hoon aur kaam ke liye tayyar hoon.\n"
        f"Aap current settings check karne ke liye /settings daba sakte hain."
    )

@app.on_message(filters.command("settings") & filters.user(Config.OWNER_ID))
async def settings_cmd(client: Client, message: Message):
    current_cmd = await db.get_active_command()
    await message.reply_text(
        f"**⚙️ Bot Settings:**\n\n"
        f"Current Leech Command: `{current_cmd}`\n\n"
        f"Change karne ke liye type karein: `/setcmd /newcmd`"
    )

@app.on_message(filters.command("setcmd") & filters.user(Config.OWNER_ID))
async def set_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Command format galat hai. Aise likhein: `/setcmd /lx`")
    
    new_cmd = message.command[1]
    await db.set_active_command(new_cmd)
    await message.reply_text(f"✅ Leech command successfully changed to: `{new_cmd}`")

async def main():
    print("Bot is starting...")
    await app.start()
    print("Bot is alive! Ready to work.")
    # Script ko zinda rakhne ke liye idle setup
    from pyrogram import idle
    await idle()
    await app.stop()

if __name__ == "__main__":
    app.run(main())
