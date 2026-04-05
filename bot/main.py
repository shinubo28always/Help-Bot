import asyncio
import os
from threading import Thread
from flask import Flask
from pyrogram import Client, filters, idle
from pyrogram.types import Message
from bot.config import Config
from bot.database import db

# ==========================================
# 1. FLASK WEB SERVER SETUP (For Hosting)
# ==========================================
web_app = Flask(__name__)

@web_app.route('/')
def home():
    # Yeh page browser par show hoga jis se hosting ko pata chalega k bot zinda hai
    return "Anime Uploader Bot is Alive and Running Successfully!"

def run_server():
    # Hosting platform automatically 'PORT' environment variable deta hai, 
    # agar na mile toh default 8080 use karega.
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# ==========================================
# 2. PYROGRAM BOT SETUP
# ==========================================
app = Client(
    "AnimeUploaderBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="bot") # Baqi files (gc_handler, uploader, basics) ko connect karega
)

# Admin panel - Settings check karna
@app.on_message(filters.command("settings") & filters.user(Config.OWNER_ID))
async def settings_cmd(client: Client, message: Message):
    current_cmd = await db.get_active_command()
    await message.reply_text(
        f"**⚙️ Bot Settings:**\n\n"
        f"Current Leech Command: `{current_cmd}`\n\n"
        f"Change karne ke liye type karein: `/setcmd /newcmd`"
    )

# Admin panel - Leech command update karna
@app.on_message(filters.command("setcmd") & filters.user(Config.OWNER_ID))
async def set_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Command format galat hai. Aise likhein: `/setcmd /lx`")
    
    new_cmd = message.command[1]
    await db.set_active_command(new_cmd)
    await message.reply_text(f"✅ Leech command successfully changed to: `{new_cmd}`")

# ==========================================
# 3. MAIN RUNNER (Bot + Server)
# ==========================================
async def main():
    print("Starting Flask Web Server...")
    # Flask ko background thread me start kar diya
    Thread(target=run_server, daemon=True).start()
    
    print("Starting Pyrogram Bot...")
    await app.start()
    print("✅ Bot is alive! Ready to work.")
    
    # Bot ko zinda rakhne ke liye
    await idle()
    await app.stop()

if __name__ == "__main__":
    # Event loop ke zariye bot start karna
    app.run(main())
