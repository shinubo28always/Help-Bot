from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.database import db
from bot.regex_parser import RegexParser
from bot.anilist import anilist_api

# Hum assume kar rahe hain ke aapka Group Chat ID yahan set hoga (Aap .env me daal sakte hain baad me)
# Abhi ke liye hum sirf owner ke bheje gaye files ko check karenge

@Client.on_message(filters.document | filters.video)
async def auto_leech_handler(client: Client, message: Message):
    # Sirf Owner/Admin ki files par react karega
    from bot.config import Config
    if message.from_user and message.from_user.id != Config.OWNER_ID:
        return

    # 1. File ka naam nikalna
    filename = ""
    if message.document:
        filename = message.document.file_name
    elif message.video:
        filename = message.video.file_name
    
    if not filename:
        return # Agar file ka naam hi nahi hai toh ignore karo

    # 2. Regex Parser se data nikalna
    parsed_data = RegexParser.parse_filename(filename)
    title = parsed_data["title"]
    ep = parsed_data["episode"]
    season = parsed_data["season"]
    quality = parsed_data["quality"] or "Unknown"

    if not title:
        return await message.reply_text("❌ File name se Anime ka title nahi mil saka.")

    # 3. Anilist par search karna
    status_msg = await message.reply_text(f"🔍 Anilist par `{title}` search kar raha hoon...")
    search_results = await anilist_api.search_anime(title)

    if not search_results:
        return await status_msg.edit_text(f"❌ Anilist par `{title}` naam ka koi anime nahi mila.")

    # 4. Agar sirf 1 exact result hai ya pehla result hum use karna chahte hain
    # (Advanced: Agar multi results ho toh buttons bhejein)
    
    if len(search_results) == 1:
        # Sirf 1 result mila
        best_anime = search_results[0]
        final_title = anilist_api.get_best_title(best_anime)
        await send_leech_command(message, status_msg, final_title, ep, season, quality)
    else:
        # Bohat saare results mile, Buttons show karo
        buttons = []
        for anime in search_results:
            anime_title = anilist_api.get_best_title(anime)
            # Callback data mein anime id aur humara parsed episode bhej rahe hain
            callback_data = f"leech_{anime['id']}_{ep}_{season}_{quality}"
            # Telegram callback data limit 64 bytes hoti hai isliye chota rakhna zaroori hai
            buttons.append([InlineKeyboardButton(anime_title, callback_data=callback_data)])
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await status_msg.edit_text(
            f"🤔 Mujhe `{title}` ke ek se zyada results mile hain. Asli Anime select karein:",
            reply_markup=reply_markup
        )

# Leech Command bhejne ka function
async def send_leech_command(message: Message, status_msg: Message, title: str, ep: str, season: str, quality: str):
    # Agar episode nahi mila regex se, toh user se mangna parega (Future step)
    if not ep:
        await status_msg.edit_text(f"⚠️ Episode number nahi mila! Please is video ka episode number reply mein likhein.")
        # User se mangne ka logic hum next step me add karenge (Conversation states)
        return

    # Database se current leech command mangwao
    active_cmd = await db.get_active_command()
    
    # Custom Caption Generate (Jaisa aapne format diya tha)
    # /l -n [AniReal - Anime] S{season}E{episode} {title} {quality}.mkv
    
    final_file_name = f"[AniReal - Anime] S{season}E{ep} {title} {quality}.mkv"
    final_command = f"{active_cmd} -n {final_file_name}"
    
    # Message ko delete karke direct reply me command bhej do
    await status_msg.delete()
    await message.reply_text(f"`{final_command}`", quote=True)
