from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot.database import db
from bot.config import Config

# ==========================================
# 1. START, HELP, ABOUT (With Buttons)
# ==========================================
@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    if not await db.is_admin(message.from_user.id):
        return await message.reply_text("⛔️ **Access Denied!**\nYeh ek private bot hai. Sirf authorized admins isay use kar sakte hain.")

    text = (
        f"👋 Hello **{message.from_user.first_name}**!\n\n"
        f"Main ek Advanced Auto-Uploader aur Leech Assistant Bot hoon. "
        f"Main akele hi GC Auto-Commander, Custom Captioning, aur Main Channel Uploading handle kar sakta hoon.\n\n"
        f"Niche diye gaye buttons par click karke details dekhein 👇"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛠 Help & Commands", callback_data="help_menu")],
        [InlineKeyboardButton("ℹ️ About Bot", callback_data="about_menu")]
    ])
    await message.reply_text(text, reply_markup=buttons)

@Client.on_callback_query(filters.regex(r"^(help_menu|about_menu|start_menu)$"))
async def menu_callbacks(client: Client, query: CallbackQuery):
    if query.data == "help_menu":
        text = (
            "🛠 **BOT COMMANDS & HELP**\n\n"
            "**General:**\n"
            "`/start` - Bot ko zinda karna\n"
            "`/settings` - Current leech command dekhna\n"
            "`/setcmd /lx` - Leech command change karna\n\n"
            "**Channel Mapping:**\n"
            "`/setcap [Title]` - Channel me add karke auto-caption set karna.\n\n"
            "**Admin Commands (Sirf Owner k liye):**\n"
            "`/addadmin [ID]` - Naya admin add karna\n"
            "`/remadmin [ID]` - Admin ko hatana\n"
            "`/admins` - Admins ki list dekhna"
        )
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="start_menu")]])
        await query.message.edit_text(text, reply_markup=buttons)

    elif query.data == "about_menu":
        text = (
            "ℹ️ **ABOUT BOT**\n\n"
            "🤖 **Name:** Anime Uploader Pro\n"
            "👨‍💻 **Developer:** Aapka Naam / Team\n"
            "⚙️ **Language:** Python 3\n"
            "📚 **Framework:** Pyrogram\n"
            "🌐 **Database:** MongoDB\n"
            "✨ **Features:** Anilist API, Regex Parsing, Auto-Post, HTML Captions."
        )
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="start_menu")]])
        await query.message.edit_text(text, reply_markup=buttons)

    elif query.data == "start_menu":
        text = f"👋 Hello **{query.from_user.first_name}**!\n\nMain ek Advanced Auto-Uploader aur Leech Assistant Bot hoon..."
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛠 Help & Commands", callback_data="help_menu")],
            [InlineKeyboardButton("ℹ️ About Bot", callback_data="about_menu")]
        ])
        await query.message.edit_text(text, reply_markup=buttons)

# ==========================================
# 2. ADMIN MANAGEMENT COMMANDS (Only for Owner)
# ==========================================
@Client.on_message(filters.command("addadmin") & filters.user(Config.OWNER_ID))
async def add_admin_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("⚠️ Format: `/addadmin [User ID]`")
    
    try:
        new_admin = int(message.command[1])
        await db.add_admin(new_admin)
        await message.reply_text(f"✅ User ID `{new_admin}` ko Admin bana diya gaya hai.")
    except ValueError:
        await message.reply_text("❌ ID sirf numbers me honi chahiye.")

@Client.on_message(filters.command("remadmin") & filters.user(Config.OWNER_ID))
async def rem_admin_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("⚠️ Format: `/remadmin [User ID]`")
    
    try:
        old_admin = int(message.command[1])
        await db.remove_admin(old_admin)
        await message.reply_text(f"✅ User ID `{old_admin}` ko Admins se hata diya gaya hai.")
    except ValueError:
        await message.reply_text("❌ ID sirf numbers me honi chahiye.")

@Client.on_message(filters.command("admins") & filters.user(Config.OWNER_ID))
async def list_admins_cmd(client: Client, message: Message):
    admins = await db.get_admins()
    if not admins:
        return await message.reply_text("⚠️ Koi external admin nahi hai. Sirf Owner admin hai.")
    
    text = "👮‍♂️ **Bot Admins List:**\n\n"
    for count, admin_id in enumerate(admins, 1):
        text += f"{count}. `{admin_id}`\n"
    
    await message.reply_text(text)
