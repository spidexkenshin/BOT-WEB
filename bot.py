"""
KENSHIN ANIME — ADMIN BOT (Fixed & Clean)
All bugs fixed — step by step upload works correctly
"""
import os, httpx
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# ── CONFIG ────────────────────────────────────────────────────────────────────
API_ID     = int(os.getenv("API_ID", "0"))
API_HASH   = os.getenv("API_HASH", "")
BOT_TOKEN  = os.getenv("BOT_TOKEN", "")
BOT_SECRET = os.getenv("BOT_SECRET", "kenshin_secret_123")
API_URL    = os.getenv("API_URL", "https://web-production-4ac21.up.railway.app")
ADMIN_IDS  = [int(x) for x in os.getenv("ADMIN_IDS", "0").split(",") if x.strip()]

bot = Client("kenshin_admin", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ── STATE STORAGE ─────────────────────────────────────────────────────────────
states = {}   # uid -> state name
udata  = {}   # uid -> collected fields dict

# ── UPLOAD STEPS (in order) ──────────────────────────────────────────────────
STEPS = [
    ("title",     "📝 *Step 1/8 — TITLE*\n\nAnime ka naam likho:\nExample: `Solo Leveling`"),
    ("tg_link",   "🔗 *Step 2/8 — TELEGRAM LINK*\n\nTelegram link daalo:\nExample: `https://t.me/+xxxxx`"),
    ("image_url", "🖼️ *Step 3/8 — POSTER IMAGE*\n\nImage URL daalo (Imgur link best rahega):\nExample: `https://i.imgur.com/abc123.jpg`\n\n_Imgur.com → upload → right click image → Copy image address_"),
    ("genre",     "🎭 *Step 4/8 — GENRE*\n\nGenre likho:\nExample: `Action • Fantasy`"),
    ("synopsis",  "📖 *Step 5/8 — SYNOPSIS*\n\nAnime ki story likho:\nExample: `Sung Jin-Woo ek weak hunter tha...`"),
    ("seasons",   "📺 *Step 6/8 — SEASONS*\n\nKitne seasons?\nExample: `2` ya `S2 Ongoing`"),
    ("episodes",  "🎬 *Step 7/8 — EPISODES*\n\nKitne episodes?\nExample: `12` ya `24`"),
    ("year",      "📅 *Step 8/8 — YEAR*\n\nRelease year:\nExample: `2024`"),
]

def is_admin(uid): return uid in ADMIN_IDS
def clear(uid): states.pop(uid, None); udata.pop(uid, None)

# ── API CALLS ─────────────────────────────────────────────────────────────────
async def api_post(ep, payload):
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(f"{API_URL}{ep}?token={BOT_SECRET}", json=payload)
        return r.json()

async def api_patch(ep, payload=None):
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.patch(f"{API_URL}{ep}?token={BOT_SECRET}", json=payload or {})
        return r.json()

async def api_delete(ep):
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.delete(f"{API_URL}{ep}?token={BOT_SECRET}")
        return r.json()

async def api_get(ep):
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(f"{API_URL}{ep}?token={BOT_SECRET}")
        return r.json()

# ── KEYBOARDS ─────────────────────────────────────────────────────────────────
def kb_category():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎌 Anime (main grid)",    callback_data="CAT_anime")],
        [InlineKeyboardButton("⭐ Featured (home page)", callback_data="CAT_featured")],
        [InlineKeyboardButton("👑 Classic (home page)",  callback_data="CAT_classic")],
        [InlineKeyboardButton("🆕 New Release (home)",   callback_data="CAT_new")],
        [InlineKeyboardButton("📖 Manwha page",          callback_data="CAT_manwha")],
        [InlineKeyboardButton("🎬 Movies page",          callback_data="CAT_movie")],
        [InlineKeyboardButton("❌ Cancel",               callback_data="CANCEL")],
    ])

def kb_tag():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 HOT",     callback_data="TAG_HOT"),
         InlineKeyboardButton("🆕 NEW",     callback_data="TAG_NEW")],
        [InlineKeyboardButton("⭐ MUST",    callback_data="TAG_MUST"),
         InlineKeyboardButton("🏆 TOP",     callback_data="TAG_TOP")],
        [InlineKeyboardButton("👑 CLASSIC", callback_data="TAG_CLASSIC"),
         InlineKeyboardButton("🔴 ONGOING", callback_data="TAG_ONGOING")],
        [InlineKeyboardButton("⬜ No Tag",  callback_data="TAG_")],
    ])

def kb_confirm():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ YES — Website pe add karo!", callback_data="CONFIRM")],
        [InlineKeyboardButton("❌ Cancel",                     callback_data="CANCEL")],
    ])

def kb_edit_fields():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1️⃣ Title",    callback_data="EF_title"),
         InlineKeyboardButton("2️⃣ TG Link",  callback_data="EF_tg_link")],
        [InlineKeyboardButton("3️⃣ Image",    callback_data="EF_image_url"),
         InlineKeyboardButton("4️⃣ Genre",    callback_data="EF_genre")],
        [InlineKeyboardButton("5️⃣ Synopsis", callback_data="EF_synopsis"),
         InlineKeyboardButton("6️⃣ Seasons",  callback_data="EF_seasons")],
        [InlineKeyboardButton("7️⃣ Episodes", callback_data="EF_episodes"),
         InlineKeyboardButton("8️⃣ Year",     callback_data="EF_year")],
        [InlineKeyboardButton("9️⃣ Tag",      callback_data="EF_tag"),
         InlineKeyboardButton("🔟 Category", callback_data="EF_category")],
        [InlineKeyboardButton("❌ Cancel",    callback_data="CANCEL")],
    ])

def kb_moveto(title):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Featured", callback_data=f"MOVE_featured__{title}")],
        [InlineKeyboardButton("👑 Classic",  callback_data=f"MOVE_classic__{title}")],
        [InlineKeyboardButton("🆕 New",      callback_data=f"MOVE_new__{title}")],
        [InlineKeyboardButton("🎌 Anime",    callback_data=f"MOVE_anime__{title}")],
        [InlineKeyboardButton("📖 Manwha",   callback_data=f"MOVE_manwha__{title}")],
        [InlineKeyboardButton("🎬 Movie",    callback_data=f"MOVE_movie__{title}")],
        [InlineKeyboardButton("❌ Cancel",   callback_data="CANCEL")],
    ])

def preview(d, cat):
    return (
        f"📋 *PREVIEW — Sab sahi hai?*\n\n"
        f"🎌 *Title:* {d.get('title','—')}\n"
        f"📂 *Category:* {cat}\n"
        f"🏷️ *Tag:* {d.get('tag','(none)')}\n"
        f"🎭 *Genre:* {d.get('genre','—')}\n"
        f"📅 *Year:* {d.get('year','—')}\n"
        f"📺 *Seasons:* {d.get('seasons','—')}\n"
        f"🎬 *Episodes:* {d.get('episodes','—')}\n"
        f"🔗 *Link:* {d.get('tg_link','—')}\n"
        f"🖼️ *Image:* {d.get('image_url','—')}\n\n"
        f"📖 *Synopsis:*\n{d.get('synopsis','—')}"
    )

# ══════════════════════════════════════════════════════════════════════════════
#  /start
# ══════════════════════════════════════════════════════════════════════════════
@bot.on_message(filters.command("start"))
async def cmd_start(_, m: Message):
    if not is_admin(m.from_user.id):
        await m.reply("❌ Access nahi hai!"); return
    name = m.from_user.first_name or "Admin"
    await m.reply(
        f"👋 *Welcome, {name}!*\n\n"
        "🎌 *KENSHIN ANIME — Admin Bot*\n\n"
        "Yahan se teri website ka poora control hai.\n\n"
        "📌 Sab commands: /help\n"
        "🚀 Anime add karne ke liye: /upload"
    )

# ══════════════════════════════════════════════════════════════════════════════
#  /help
# ══════════════════════════════════════════════════════════════════════════════
@bot.on_message(filters.command("help"))
async def cmd_help(_, m: Message):
    if not is_admin(m.from_user.id): return
    await m.reply(
        "📖 *KENSHIN ANIME BOT — ALL COMMANDS*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📤 *UPLOAD*\n"
        "`/upload` — Anime add (step by step)\n"
        "`/uploadmanwha` — Manwha add\n"
        "`/uploadmovie` — Movie add\n\n"
        "✏️ *EDIT*\n"
        "`/edit` — Koi bhi anime edit karo\n"
        "`/editfeatured` — Featured wale edit karo\n"
        "`/editclassic` — Classics edit karo\n"
        "`/editnew` — New releases edit karo\n"
        "`/editmanwha` — Manwha edit karo\n"
        "`/editmovie` — Movies edit karo\n\n"
        "📂 *MOVE TO CATEGORY*\n"
        "`/setfeatured` — Featured mein move karo\n"
        "`/setclassic` — Classic mein move karo\n"
        "`/setnew` — New releases mein move karo\n"
        "`/moveto` — Kisi bhi category mein move\n\n"
        "🗑️ *DELETE*\n"
        "`/delete` — Permanently delete\n"
        "`/hide` — Website se chhupa do (recoverable)\n"
        "`/unhide` — Wapas dikhao\n\n"
        "📋 *LIST & STATS*\n"
        "`/list` — Sab anime ki list\n"
        "`/listcat anime` — Category wise list\n"
        "`/stats` — Total counts\n\n"
        "🖼️ *LOGO*\n"
        "`/setlogo` — Website ka logo update karo\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Start karo: /upload"
    )

# ══════════════════════════════════════════════════════════════════════════════
#  UPLOAD — Step by step
# ══════════════════════════════════════════════════════════════════════════════
@bot.on_message(filters.command(["upload", "uploadmanwha", "uploadmovie"]))
async def cmd_upload(_, m: Message):
    if not is_admin(m.from_user.id): return
    uid = m.from_user.id
    clear(uid)
    cmd = m.command[0].lower()
    preset = {"uploadmanwha": "manwha", "uploadmovie": "movie"}.get(cmd, None)
    udata[uid] = {"_cat": preset}

    if preset:
        states[uid] = "step_0"
        await m.reply(STEPS[0][1])
    else:
        states[uid] = "choose_cat"
        await m.reply("📂 *Pehle category choose karo:*", reply_markup=kb_category())

# Category callback
@bot.on_callback_query(filters.regex(r"^CAT_(.+)$"))
async def cb_cat(_, cb):
    uid = cb.from_user.id
    if not is_admin(uid): return
    cat = cb.matches[0].group(1)
    udata[uid]["_cat"] = cat
    states[uid] = "step_0"
    await cb.message.edit(f"✅ Category: *{cat}*\n\n" + STEPS[0][1])

# Cancel callback
@bot.on_callback_query(filters.regex("^CANCEL$"))
async def cb_cancel(_, cb):
    uid = cb.from_user.id
    clear(uid)
    await cb.message.edit("❌ Cancelled. /upload se dobara shuru karo.")

# Tag callback → show preview
@bot.on_callback_query(filters.regex(r"^TAG_(.*)$"))
async def cb_tag(_, cb):
    uid = cb.from_user.id
    if not is_admin(uid): return
    tag = cb.matches[0].group(1)
    udata[uid]["tag"] = tag
    cat = udata[uid].get("_cat", "anime")
    states[uid] = "confirming"
    await cb.message.edit(preview(udata[uid], cat), reply_markup=kb_confirm())

# Confirm callback → POST to API
@bot.on_callback_query(filters.regex("^CONFIRM$"))
async def cb_confirm(_, cb):
    uid = cb.from_user.id
    if not is_admin(uid): return
    d = udata.get(uid, {})
    payload = {
        "title":     d.get("title", ""),
        "genre":     d.get("genre", ""),
        "tag":       d.get("tag", ""),
        "image_url": d.get("image_url", ""),
        "tg_link":   d.get("tg_link", ""),
        "seasons":   d.get("seasons", "1"),
        "episodes":  d.get("episodes", "12"),
        "year":      d.get("year", "2024"),
        "synopsis":  d.get("synopsis", ""),
        "category":  d.get("_cat", "anime"),
        "visible":   True,
    }
    await cb.message.edit("⏳ Database mein add kar raha hoon...")
    try:
        result = await api_post("/admin/add", payload)
        await cb.message.edit(
            result.get("msg", "❌ Unknown error") +
            "\n\n🌐 Website pe 1-2 second mein dikh jaayega!\n\nAur anime add karne ke liye: /upload"
        )
    except Exception as e:
        await cb.message.edit(f"❌ API Error: {e}\n\nCheck karo API_URL sahi set hai ya nahi.")
    clear(uid)

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN MESSAGE HANDLER
# ══════════════════════════════════════════════════════════════════════════════
ALL_COMMANDS = [
    "start","help","upload","uploadmanwha","uploadmovie",
    "edit","editfeatured","editclassic","editnew","editmanwha","editmovie",
    "delete","hide","unhide","list","listcat","stats",
    "moveto","setfeatured","setclassic","setnew","setlogo"
]

@bot.on_message(filters.text & ~filters.command(ALL_COMMANDS))
async def handle_steps(_, m: Message):
    if not is_admin(m.from_user.id): return
    uid = m.from_user.id
    state = states.get(uid)
    txt = m.text.strip()

    if not state:
        return  # No active flow

    if txt.lower() == "/cancel":
        clear(uid)
        await m.reply("❌ Cancelled.")
        return

    # ── UPLOAD STEPS ─────────────────────────────────────────────────────────
    if state.startswith("step_"):
        step_num = int(state.split("_")[1])
        key, _ = STEPS[step_num]
        udata[uid][key] = txt
        nxt = step_num + 1

        if nxt < len(STEPS):
            states[uid] = f"step_{nxt}"
            await m.reply(STEPS[nxt][1])
        else:
            # All 8 steps done → ask tag
            states[uid] = "step_tag"
            await m.reply("🏷️ *Tag/Badge choose karo:*", reply_markup=kb_tag())
        return

    # ── EDIT FIELD VALUE ─────────────────────────────────────────────────────
    if state == "editing_field":
        field = udata[uid].get("_edit_field", "")
        title = udata[uid].get("_edit_title", "")
        if not field or not title:
            await m.reply("❌ Error. /edit se dobara karo.")
            clear(uid); return
        msg = await m.reply("⏳ Updating...")
        try:
            result = await api_patch(f"/admin/edit/{title}", {"field": field, "value": txt})
            await msg.edit(result.get("msg", "❌ Error"))
        except Exception as e:
            await msg.edit(f"❌ API Error: {e}")
        clear(uid)
        return

    # ── WAITING FOR ANIME NAME (edit) ─────────────────────────────────────────
    if state == "wait_edit_title":
        udata[uid]["_edit_title"] = txt
        states[uid] = "choosing_edit_field"
        await m.reply(
            f"✏️ Editing: *{txt}*\n\nKonsa field change karna?",
            reply_markup=kb_edit_fields()
        )
        return

    # ── WAITING FOR NAME (delete) ─────────────────────────────────────────────
    if state == "wait_delete":
        msg = await m.reply(f"⏳ '{txt}' delete kar raha hoon...")
        try:
            result = await api_delete(f"/admin/delete/{txt}")
            await msg.edit(result.get("msg", "❌ Error"))
        except Exception as e:
            await msg.edit(f"❌ API Error: {e}")
        clear(uid)
        return

    # ── WAITING FOR NAME (hide) ───────────────────────────────────────────────
    if state == "wait_hide":
        msg = await m.reply(f"⏳ Hiding '{txt}'...")
        try:
            result = await api_patch(f"/admin/hide/{txt}")
            await msg.edit(result.get("msg", "❌ Error"))
        except Exception as e:
            await msg.edit(f"❌ API Error: {e}")
        clear(uid)
        return

    # ── WAITING FOR NAME (unhide) ─────────────────────────────────────────────
    if state == "wait_unhide":
        msg = await m.reply(f"⏳ Unhiding '{txt}'...")
        try:
            result = await api_patch(f"/admin/show/{txt}")
            await msg.edit(result.get("msg", "❌ Error"))
        except Exception as e:
            await msg.edit(f"❌ API Error: {e}")
        clear(uid)
        return

    # ── WAITING FOR NAME (moveto) ─────────────────────────────────────────────
    if state == "wait_moveto":
        states[uid] = "choosing_moveto_cat"
        await m.reply(f"📂 *'{txt}'* ko kahan move karna?", reply_markup=kb_moveto(txt))
        return

    # ── LOGO URL ──────────────────────────────────────────────────────────────
    if state == "wait_logo":
        udata[uid]["logo_url"] = txt
        await m.reply(
            f"✅ Logo URL save ho gaya!\n\n"
            f"`{txt}`\n\n"
            f"Ab website ki `index.html` mein ye line dhundho:\n"
            f"`const LOGO_URL = \"\";`\n\n"
            f"Aur isme ye URL daalo:\n"
            f"`const LOGO_URL = \"{txt}\";`\n\n"
            f"Phir Netlify pe file re-upload karo. Done! ✅"
        )
        clear(uid)
        return

# ── EDIT FIELD CALLBACK ────────────────────────────────────────────────────────
@bot.on_callback_query(filters.regex(r"^EF_(.+)$"))
async def cb_edit_field(_, cb):
    uid = cb.from_user.id
    if not is_admin(uid): return
    field = cb.matches[0].group(1)
    udata[uid]["_edit_field"] = field
    states[uid] = "editing_field"
    prompts = {
        "title": "📝 Naya title daalo:",
        "tg_link": "🔗 Naya Telegram link daalo:",
        "image_url": "🖼️ Nayi image URL daalo:",
        "genre": "🎭 Naya genre daalo:",
        "synopsis": "📖 Nayi synopsis daalo:",
        "seasons": "📺 Seasons update karo:",
        "episodes": "🎬 Episodes update karo:",
        "year": "📅 Naya year daalo:",
        "tag": "🏷️ Naya tag daalo (HOT/NEW/CLASSIC/MUST/TOP/ONGOING ya blank ke liye - likho):",
        "category": "📂 Nayi category daalo:\n`anime` `featured` `classic` `new` `manwha` `movie`",
    }
    await cb.message.edit(prompts.get(field, f"Naya {field} daalo:"))

# ── MOVE CALLBACK ─────────────────────────────────────────────────────────────
@bot.on_callback_query(filters.regex(r"^MOVE_(\w+)__(.+)$"))
async def cb_move(_, cb):
    uid = cb.from_user.id
    if not is_admin(uid): return
    cat   = cb.matches[0].group(1)
    title = cb.matches[0].group(2)
    await cb.message.edit(f"⏳ Moving '{title}' to '{cat}'...")
    try:
        result = await api_patch(f"/admin/move/{title}?category={cat}")
        await cb.message.edit(result.get("msg", "❌ Error"))
    except Exception as e:
        await cb.message.edit(f"❌ API Error: {e}")
    clear(uid)

# ══════════════════════════════════════════════════════════════════════════════
#  EDIT COMMANDS
# ══════════════════════════════════════════════════════════════════════════════
async def start_edit(m: Message, cat_filter=None):
    uid = m.from_user.id
    if not is_admin(uid): return
    clear(uid)
    if cat_filter:
        items = await api_get(f"/anime/category/{cat_filter}" if False else f"/admin/list")
        # filter locally
        items = [i for i in items if i.get("category") == cat_filter]
        if not items:
            await m.reply(f"📭 {cat_filter} mein koi anime nahi hai!")
            return
        txt = f"✏️ *{cat_filter.upper()} — Konsa edit karna?*\nExactly naam copy karke bhejo:\n\n"
        txt += "\n".join(f"• `{i['title']}`" for i in items)
        await m.reply(txt)
    else:
        await m.reply("✏️ *EDIT*\n\nKis anime ka naam hai?\n(Exactly waise likhna jaisa database mein hai)\n\n💡 Naam check karne ke liye: /list")
    states[uid] = "wait_edit_title"

@bot.on_message(filters.command("edit"))
async def cmd_edit(_, m): await start_edit(m)
@bot.on_message(filters.command("editfeatured"))
async def cmd_ef(_, m): await start_edit(m, "featured")
@bot.on_message(filters.command("editclassic"))
async def cmd_ec(_, m): await start_edit(m, "classic")
@bot.on_message(filters.command("editnew"))
async def cmd_en(_, m): await start_edit(m, "new")
@bot.on_message(filters.command("editmanwha"))
async def cmd_em(_, m): await start_edit(m, "manwha")
@bot.on_message(filters.command("editmovie"))
async def cmd_emv(_, m): await start_edit(m, "movie")

# ══════════════════════════════════════════════════════════════════════════════
#  MOVE COMMANDS
# ══════════════════════════════════════════════════════════════════════════════
@bot.on_message(filters.command(["moveto", "setfeatured", "setclassic", "setnew"]))
async def cmd_move(_, m: Message):
    uid = m.from_user.id
    if not is_admin(uid): return
    clear(uid)
    cmd = m.command[0].lower()
    quick = {"setfeatured": "featured", "setclassic": "classic", "setnew": "new"}
    if cmd in quick:
        udata[uid] = {"_quick_cat": quick[cmd]}
    states[uid] = "wait_moveto"
    await m.reply(f"📝 Konsa anime move karna hai? Naam likho:")

# ══════════════════════════════════════════════════════════════════════════════
#  DELETE / HIDE / UNHIDE
# ══════════════════════════════════════════════════════════════════════════════
@bot.on_message(filters.command("delete"))
async def cmd_del(_, m: Message):
    uid = m.from_user.id
    if not is_admin(uid): return
    clear(uid); states[uid] = "wait_delete"
    await m.reply("🗑️ *DELETE*\n\nKonsa anime delete karna?\n(Naam exactly likhna)\n\n⚠️ Ye permanent hai!")

@bot.on_message(filters.command("hide"))
async def cmd_hide(_, m: Message):
    uid = m.from_user.id
    if not is_admin(uid): return
    clear(uid); states[uid] = "wait_hide"
    await m.reply("👁️ *HIDE*\n\nKonsa anime hide karna?")

@bot.on_message(filters.command("unhide"))
async def cmd_unhide(_, m: Message):
    uid = m.from_user.id
    if not is_admin(uid): return
    clear(uid); states[uid] = "wait_unhide"
    await m.reply("✅ *UNHIDE*\n\nKonsa anime wapas dikhana?")

# ══════════════════════════════════════════════════════════════════════════════
#  LIST / STATS
# ══════════════════════════════════════════════════════════════════════════════
@bot.on_message(filters.command("list"))
async def cmd_list(_, m: Message):
    if not is_admin(m.from_user.id): return
    msg = await m.reply("⏳ List aa rahi hai...")
    try:
        items = await api_get("/admin/list")
        if not items:
            await msg.edit("📭 Database bilkul empty hai! /upload se add karo."); return
        text = f"📋 *FULL LIST ({len(items)} items)*\n\n"
        for i in items:
            st = "✅" if i.get("visible") else "👁️hidden"
            text += f"{st} `{i['title']}` [{i.get('category','?')}] {i.get('tag','')}\n"
        if len(text) > 4000:
            for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
                await m.reply(chunk)
            await msg.delete()
        else:
            await msg.edit(text)
    except Exception as e:
        await msg.edit(f"❌ Error: {e}")

@bot.on_message(filters.command("listcat"))
async def cmd_listcat(_, m: Message):
    if not is_admin(m.from_user.id): return
    if len(m.command) < 2:
        await m.reply("Format: `/listcat featured`\nOptions: `anime` `featured` `classic` `new` `manwha` `movie`")
        return
    cat = m.command[1].lower()
    msg = await m.reply(f"⏳ {cat} list aa rahi hai...")
    try:
        all_items = await api_get("/admin/list")
        items = [i for i in all_items if i.get("category") == cat]
        if not items:
            await msg.edit(f"📭 '{cat}' mein kuch nahi hai!"); return
        text = f"📋 *{cat.upper()} ({len(items)})*\n\n"
        text += "\n".join(f"• `{i['title']}` {i.get('tag','')}" for i in items)
        await msg.edit(text)
    except Exception as e:
        await msg.edit(f"❌ Error: {e}")

@bot.on_message(filters.command("stats"))
async def cmd_stats(_, m: Message):
    if not is_admin(m.from_user.id): return
    msg = await m.reply("⏳...")
    try:
        d = await api_get("/stats")
        await msg.edit(
            f"📊 *KENSHIN ANIME STATS*\n\n"
            f"🎌 Total Titles: *{d.get('total',0)}*\n"
            f"📖 Manwha: *{d.get('manwha',0)}*\n"
            f"🎬 Movies: *{d.get('movies',0)}*\n\n"
            f"🌐 Website: kenshinanimehindi.42web.io"
        )
    except Exception as e:
        await msg.edit(f"❌ Error: {e}")

# ══════════════════════════════════════════════════════════════════════════════
#  /setlogo — Logo update karo
# ══════════════════════════════════════════════════════════════════════════════
@bot.on_message(filters.command("setlogo"))
async def cmd_setlogo(_, m: Message):
    uid = m.from_user.id
    if not is_admin(uid): return
    clear(uid)
    states[uid] = "wait_logo"
    await m.reply(
        "🖼️ *SET WEBSITE LOGO*\n\n"
        "Logo image ka URL daalo:\n\n"
        "URL kahan se milega?\n"
        "1. Imgur.com pe image upload karo\n"
        "2. Right click → Copy image address\n"
        "3. Woh URL yahan bhejo\n\n"
        "Example: `https://i.imgur.com/abc123.png`"
    )

# ── RUN ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🤖 Kenshin Admin Bot starting...")
    bot.run()
