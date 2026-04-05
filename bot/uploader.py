from pyrogram import Client, filters
from pyrogram.types import Message
from bot.database import db
from bot.regex_parser import RegexParser
from bot.config import Config

# ==========================================
# 1. CHANNEL MAPPING (Caption & Channel Set Karna)
# ==========================================
@Client.on_message(filters.command("setcap") & filters.channel)
async def set_caption_cmd(client: Client, message: Message):
    # Message ka text nikalna
    text = message.text or message.caption
    lines = text.split("\n", 1) # Pehli line command ke liye, baqi lines caption ke liye
    
    cmd_line = lines[0].split(" ", 1)
    
    # Agar command me title diya hai (e.g. /setcap Fairy Tail), toh woh le lo
    if len(cmd_line) > 1:
        anime_title = cmd_line[1].strip()
    else:
        # Agar sirf /setcap likha hai, toh channel ke naam se title bana lo
        raw_title = message.chat.title
        anime_title = raw_title.lower().replace("hindi", "").replace("dubbed", "").replace("subbed", "").strip()

    # Agar doosri line nahi hai, toh default caption laga do
    caption_template = lines[1] if len(lines) > 1 else "<b>{title}</b>\nEpisode: {ep} [{season}]\nQuality: {quality}"
    
    # Database me save kar diya
    await db.set_channel_map(anime_title, message.chat.id, caption_template)
    
    # Message ko channel se delete kar diya taake channel clean rahe
    await message.delete()
    
    # Owner ko PM me confirm message bhej diya
    await client.send_message(Config.OWNER_ID, f"✅ **Channel Mapped Successfully!**\n\nChannel: `{message.chat.title}`\nAnime Mapped: `{anime_title}`\nCaption Saved!")


# ==========================================
# 2. AUTO UPLOAD TO CHANNEL & ANNOUNCEMENT
# ==========================================
@Client.on_message(filters.private & (filters.document | filters.video) & filters.user(Config.OWNER_ID))
@Client.on_message(filters.private & (filters.document | filters.video))
async def handle_final_upload(client: Client, message: Message):
    # Ab function ke andar admin check karein
    if not await db.is_admin(message.from_user.id):
        return
async def handle_final_upload(client: Client, message: Message):
    # Sirf us file par kaam karega jisme hamara tag "[AniReal" ho (taake regular files ignore hon)
    filename = message.document.file_name if message.document else message.video.file_name
    if not filename or "[AniReal" not in filename:
        return
        
    status_msg = await message.reply_text("⏳ Processing for Auto-Upload...")

    # File Name se Data nikalna
    parsed = RegexParser.parse_filename(filename)
    title = parsed["title"]
    ep = parsed["episode"]
    season = parsed["season"]
    quality = parsed["quality"]
    
    # Database se Check karna ke kya yeh Anime kisi channel se connected hai?
    channel_data = await db.get_channel_map(title)
    if not channel_data:
        return await status_msg.edit_text(
            f"❌ `{title}` ka koi Channel Database mein nahi mila!\n"
            f"Pehle Us Anime ke channel mein Bot ko admin banayein aur yeh send karein:\n\n"
            f"`/setcap {title}`\n`Episode : {{ep}}`\n`Quality : {{quality}}`"
        )
        
    # Custom Caption Taiyar karna (HTML format ke sath)
    try:
        final_caption = channel_data["caption"].format(
            title=title, ep=ep, season=season, quality=quality
        )
    except KeyError as e:
        return await status_msg.edit_text(f"❌ Caption template mein ghalati hai. Missing Tag: {e}")

    # File ko Specific Anime Channel me Copy (Upload) karna
    try:
        # Message.copy se file direct forward hoti hai bina download kiye (0 Data usage & Super Fast)
        uploaded_msg = await message.copy(
            chat_id=channel_data["channel_id"],
            caption=final_caption,
            # HTML parsing on rakhna taake Bold/Italic kaam kare
            parse_mode=None # Pyrogram default par HTML aur Markdown dono allow karta hai
        )
        
        # Main Channel me Announcement Post karna
        if Config.MAIN_CHANNEL_ID:
            main_text = (
                f"🆕 **New Anime Episode Added!**\n\n"
                f"📺 **Anime:** {title}\n"
                f"🔢 **Episode:** {ep}\n"
                f"🌟 **Quality:** {quality}\n\n"
                f"👉 [Click Here to Watch Episode]({uploaded_msg.link})"
            )
            # Disable web page preview taake neat lage
            await client.send_message(Config.MAIN_CHANNEL_ID, main_text, disable_web_page_preview=True)
            
        await status_msg.edit_text(f"✅ **Success!**\nFile `{title}` ke channel me upload ho gayi aur Main Channel me alert chala gaya.")
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Upload failed: `{e}`\nCheck karein ke kya Bot Channel mein Admin hai?")
