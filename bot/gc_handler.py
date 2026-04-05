from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot.database import db
from bot.regex_parser import RegexParser
from bot.anilist import anilist_api
from bot.config import Config

# BOT KI MEMORY (State Management): Yeh yaad rakhega ke kis user se Episode mangna baki hai
WAITING_FOR_EPISODE = {} 

@Client.on_message(filters.document | filters.video)
async def auto_leech_handler(client: Client, message: Message):
    if message.from_user and message.from_user.id != Config.OWNER_ID:
        return

    if not message.from_user or not await db.is_admin(message.from_user.id):
    return
    
    filename = message.document.file_name if message.document else message.video.file_name
    if not filename:
        return 

    parsed_data = RegexParser.parse_filename(filename)
    title = parsed_data["title"]
    ep = parsed_data["episode"]
    season = parsed_data["season"]
    quality = parsed_data["quality"] or "Unknown"

    if not title:
        return await message.reply_text("❌ File name se Anime ka title nahi mil saka.")

    status_msg = await message.reply_text(f"🔍 Anilist par `{title}` search kar raha hoon...")
    search_results = await anilist_api.search_anime(title)

    if not search_results:
        return await status_msg.edit_text(f"❌ Anilist par `{title}` naam ka koi anime nahi mila.")

    if len(search_results) == 1:
        best_anime = search_results[0]
        final_title = anilist_api.get_best_title(best_anime)
        await process_and_send_command(message, status_msg, final_title, ep, season, quality)
    else:
        buttons = []
        for anime in search_results:
            anime_title = anilist_api.get_best_title(anime)
            # Ep agar None hai toh usko "None" text bana denge taake button me error na aaye
            safe_ep = ep if ep else "None"
            callback_data = f"leech_{anime['id']}_{safe_ep}_{season}_{quality}"
            buttons.append([InlineKeyboardButton(anime_title, callback_data=callback_data)])
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await status_msg.edit_text(
            f"🤔 Mujhe `{title}` ke zyada results mile hain. Asli Anime select karein:",
            reply_markup=reply_markup
        )


# --- NAYA FEATURE 1: BUTTON CLICK KAISE KAAM KAREGA ---
@Client.on_callback_query(filters.regex(r"^leech_"))
async def on_anime_select(client: Client, callback_query: CallbackQuery):
    # Data nikalna (e.g., leech_12345_03_1_1080p)
    _, anime_id, ep, season, quality = callback_query.data.split("_")
    
    if ep == "None":
        ep = None # Wapis Python ke None me convert kar diya

    # ID se Title mangwana
    anime_data = await anilist_api.get_anime_by_id(int(anime_id))
    final_title = anilist_api.get_best_title(anime_data)

    # Ab command bhejne wale function ko call kar do
    await process_and_send_command(
        callback_query.message.reply_to_message, # Original file wala message
        callback_query.message, # Button wala message
        final_title, ep, season, quality
    )


# --- CORE LOGIC: COMMAND BHEJNA YA EPISODE MANGNA ---
async def process_and_send_command(original_message: Message, status_msg: Message, title: str, ep: str, season: str, quality: str):
    user_id = original_message.from_user.id

    # Agar Episode nahi mila, toh Bot wait karega aur User se mangega
    if not ep:
        # Bot ki memory mein data save kar liya
        WAITING_FOR_EPISODE[user_id] = {
            "original_message": original_message,
            "title": title,
            "season": season,
            "quality": quality,
            "status_msg": status_msg
        }
        await status_msg.edit_text(f"⚠️ `{title}` ka **Episode Number** nahi mila!\n\n👇 Please mujhe sirf episode number (jaise `01`, `12`) likh kar bhejein.")
        return

    # Agar sab kuch mojood hai, toh final command bhej do
    active_cmd = await db.get_active_command()
    final_file_name = f"[AniReal - Anime] S{season}E{ep} {title} {quality}.mkv"
    final_command = f"{active_cmd} -n {final_file_name}"
    
    await status_msg.delete()
    await original_message.reply_text(f"`{final_command}`", quote=True)


# --- NAYA FEATURE 2: JAB USER EPISODE NUMBER BHEJEGA ---
@Client.on_message(filters.text & filters.user(Config.OWNER_ID))
async def catch_episode_number(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check karein kya bot is user se episode ka wait kar raha hai?
    if user_id in WAITING_FOR_EPISODE:
        ep = message.text.strip()
        
        # Check karein ke user ne number hi bheja hai na
        if not ep.isdigit():
            return await message.reply_text("❌ Galat format. Sirf number bhejein (jaise: `05` ya `12`).")
            
        # Agar number theek hai, toh zero padding lagayein (e.g. 5 ko 05 bana de)
        if len(ep) == 1:
             ep = f"0{ep}"

        # Memory se data bahar nikal lein
        data = WAITING_FOR_EPISODE.pop(user_id)
        original_message = data["original_message"]
        title = data["title"]
        season = data["season"]
        quality = data["quality"]
        status_msg = data["status_msg"]

        # Final command banayein
        active_cmd = await db.get_active_command()
        final_file_name = f"[AniReal - Anime] S{season}E{ep} {title} {quality}.mkv"
        final_command = f"{active_cmd} -n {final_file_name}"
        
        # Message delete karke original file par command reply karein
        await status_msg.delete()
        await message.delete() # Aapne jo number likha tha, us message ko bhi delete kar dega for clean chat
        await original_message.reply_text(f"`{final_command}`", quote=True)
