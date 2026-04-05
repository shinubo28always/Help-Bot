from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot.database import db
from bot.regex_parser import RegexParser
from bot.anilist import anilist_api
from bot.config import Config
import asyncio

# BOT KI MEMORY (State Management): Yeh yaad rakhega ke kis user se Episode mangna baki hai
WAITING_FOR_EPISODE = {} 

@Client.on_message(filters.document | filters.video)
async def auto_leech_handler(client: Client, message: Message):
    if not message.from_user:
        return

    if not await db.is_admin(message.from_user.id):
        return
    
    filename = message.document.file_name if message.document else message.video.file_name
    if not filename:
        return 

    # AGAR FILE PEHLE SE HI "[AniReal" KI HAI, TOH IS HANDLER KO CHOD DO
    if "[AniReal" in filename:
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

    # SPECIAL TECHNIQUE: Auto-proceed if exact match or only one result
    best_match = None
    if len(search_results) == 1:
        best_match = search_results[0]
    else:
        # Check for EXACT match (case insensitive)
        for res in search_results:
            titles = [res["title"]["romaji"].lower()]
            if res["title"]["english"]:
                titles.append(res["title"]["english"].lower())

            if title.lower() in titles:
                best_match = res
                break

    if best_match:
        final_title = anilist_api.get_best_title(best_match)
        # Poster ke saath auto confirm karein
        await status_msg.delete()

        poster = best_match.get("coverImage", {}).get("large")
        if poster:
            status_msg = await message.reply_photo(
                photo=poster,
                caption=f"✅ **Auto-Matched:** `{final_title}`\n⏳ Processing..."
            )
        else:
            status_msg = await message.reply_text(f"✅ **Auto-Matched:** `{final_title}`\n⏳ Processing...")

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
        ep = None

    # ID se Title mangwana
    anime_data = await anilist_api.get_anime_by_id(int(anime_id))
    final_title = anilist_api.get_best_title(anime_data)

    # Poster dikhayen
    poster = anime_data.get("coverImage", {}).get("large")

    if poster:
        # Edit existing message to show poster and info
        await callback_query.message.delete()
        new_status_msg = await callback_query.message.reply_to_message.reply_photo(
            photo=poster,
            caption=f"✅ **Selected:** `{final_title}`\n⏳ Processing..."
        )
    else:
        new_status_msg = await callback_query.message.edit_text(f"✅ **Selected:** `{final_title}`\n⏳ Processing...")

    # Ab command bhejne wale function ko call kar do
    await process_and_send_command(
        callback_query.message.reply_to_message,
        new_status_msg,
        final_title, ep, season, quality
    )


# --- CORE LOGIC: COMMAND BHEJNA YA EPISODE MANGNA ---
async def process_and_send_command(original_message: Message, status_msg: Message, title: str, ep: str, season: str, quality: str):
    user_id = original_message.from_user.id

    if not ep:
        WAITING_FOR_EPISODE[user_id] = {
            "original_message": original_message,
            "title": title,
            "season": season,
            "quality": quality,
            "status_msg": status_msg
        }
        prompt_text = f"⚠️ `{title}` ka **Episode Number** nahi mila!\n\n👇 Please mujhe sirf episode number (jaise `01`, `12`) likh kar bhejein."
        if status_msg.caption:
            await status_msg.edit_caption(prompt_text)
        else:
            await status_msg.edit_text(prompt_text)
        return

    active_cmd = await db.get_active_command()
    final_file_name = f"[AniReal - Anime] S{season}E{ep} {title} {quality}.mkv"
    final_command = f"{active_cmd} -n {final_file_name}"
    
    await status_msg.delete()
    await original_message.reply_text(f"`{final_command}`", quote=True)


# --- NAYA FEATURE 2: JAB USER EPISODE NUMBER BHEJEGA ---
@Client.on_message(filters.text & filters.user(Config.OWNER_ID))
async def catch_episode_number(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id in WAITING_FOR_EPISODE:
        ep = message.text.strip()
        
        if not ep.isdigit():
            return await message.reply_text("❌ Galat format. Sirf number bhejein (jaise: `05` ya `12`).")
            
        if len(ep) == 1:
             ep = f"0{ep}"

        data = WAITING_FOR_EPISODE.pop(user_id)
        original_message = data["original_message"]
        title = data["title"]
        season = data["season"]
        quality = data["quality"]
        status_msg = data["status_msg"]

        active_cmd = await db.get_active_command()
        final_file_name = f"[AniReal - Anime] S{season}E{ep} {title} {quality}.mkv"
        final_command = f"{active_cmd} -n {final_file_name}"
        
        await status_msg.delete()
        await message.delete()
        await original_message.reply_text(f"`{final_command}`", quote=True)
