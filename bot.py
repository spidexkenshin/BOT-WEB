"""
KENSHIN ANIME — COMPLETE ADMIN BOT
Step-by-step upload process
Railway pe deploy hoga
"""
import os, httpx
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# ── CONFIG ────────────────────────────────────────────────────────────────────
API_ID     = int(os.getenv("API_ID", "0"))
API_HASH   = os.getenv("API_HASH", "")
BOT_TOKEN  = os.getenv("BOT_TOKEN", "")
BOT_SECRET = os.getenv("BOT_SECRET", "kenshin_secret_123")
API_URL    = os.getenv("API_URL", "https://your-api.railway.app")
ADMIN_IDS  = [int(x) for x in os.getenv("ADMIN_IDS", "0").split(",")]

bot = Client("kenshin_admin", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ── CONVERSATION STATE ────────────────────────────────────────────────────────
# Har user ka current step aur data store hoga yahan
states = {}   # user_id -> current step name
data   = {}   # user_id -> dict of collected fields

UPLOAD_STEPS = [
    ("name",     "📝 **Step 1/8 — TITLE**\n\nAnime ka naam likho:\n\nExample: `Solo Leveling Season 2`"),
    ("tg_link",  "🔗 **Step 2/8 — TELEGRAM LINK**\n\nTelegram channel/post ka link daalo:\n\nExample: `https://t.me/+xxxxx`"),
    ("image_url","🖼️ **Step 3/8 — POSTER IMAGE**\n\nImage ka URL daalo (Imgur ya koi bhi direct image link):\n\nExample: `https://i.imgur.com/abc123.jpg`\n\n_Tip: Imgur pe upload karo → right click → copy image address_"),
    ("genre",    "🎭 **Step 4/8 — GENRES**\n\nGenres likho (comma se alag karo):\n\nExample: `Action • Fantasy • Adventure`"),
    ("synopsis", "📖 **Step 5/8 — SYNOPSIS**\n\nAnime ki story/description likho:\n\nExample: `Sung Jin-Woo, duniya ka sabse weak hunter hai...`"),
    ("seasons",  "📺 **Step 6/8 — SEASONS**\n\nKitne seasons hain?\n\nExample: `2` ya `S2 Ongoing` ya `Complete (3 Seasons)`"),
    ("episodes", "🎬 **Step 7/8 — EPISODES**\n\nKitne episodes?\n\nExample: `12` ya `24 Episodes` ya `Ongoing`"),
    ("year",     "📅 **Step 8/8 — YEAR**\n\nRelease year:\n\nExample: `2024`"),
]

EDIT_FIELDS = {
    "1": ("title",    "📝 Naya title daalo:"),
    "2": ("tg_link",  "🔗 Naya Telegram link daalo:"),
    "3": ("image_url","🖼️ Naya image URL daalo:"),
    "4": ("genre",    "🎭 Naya genre daalo:"),
    "5": ("synopsis", "📖 Nayi synopsis daalo:"),
    "6": ("seasons",  "📺 Seasons update karo:"),
    "7": ("episodes", "🎬 Episodes update karo:"),
    "8": ("year",     "📅 Naya year daalo:"),
    "9": ("tag",      "🏷️ Naya tag daalo (HOT/NEW/CLASSIC/MUST/TOP ya blank ke liye - daalo):"),
    "10":("category", "📂 Nayi category daalo:\n`anime` `featured` `classic` `new` `manwha` `movie`"),
}

# ── HELPERS ───────────────────────────────────────────────────────────────────
def is_admin(uid): return uid in ADMIN_IDS

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

def clear_state(uid):
    states.pop(uid, None)
    data.pop(uid, None)

def category_keyboard(current_cmd):
    """Category select karne ke liye buttons"""
    cats = [
        ("🎌 Anime", "anime"),
        ("⭐ Featured", "featured"),
        ("👑 Classic", "classic"),
        ("🆕 New Release", "new"),
        ("📖 Manwha", "manwha"),
        ("🎬 Movie", "movie"),
    ]
    buttons = []
    for label, val in cats:
        buttons.append([InlineKeyboardButton(label, callback_data=f"cat_{val}_{current_cmd}")])
    return InlineKeyboardMarkup(buttons)

def tag_keyboard():
    tags = [("🔥 HOT","HOT"),("🆕 NEW","NEW"),("⭐ MUST","MUST"),
            ("🏆 TOP","TOP"),("👑 CLASSIC","CLASSIC"),("🔴 ONGOING","ONGOING"),("⬜ None","")]
    btns = [[InlineKeyboardButton(l, callback_data=f"tag_{v}")] for l,v in tags]
    return InlineKeyboardMarkup(btns)

def confirm_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm — Add Karo!", callback_data="confirm_add")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
    ])

def edit_field_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1. Title",    callback_data="ef_1"),
         InlineKeyboardButton("2. TG Link",  callback_data="ef_2")],
        [InlineKeyboardButton("3. Image",    callback_data="ef_3"),
         InlineKeyboardButton("4. Genre",    callback_data="ef_4")],
        [InlineKeyboardButton("5. Synopsis", callback_data="ef_5"),
         InlineKeyboardButton("6. Seasons",  callback_data="ef_6")],
        [InlineKeyboardButton("7. Episodes", callback_data="ef_7"),
         InlineKeyboardButton("8. Year",     callback_data="ef_8")],
        [InlineKeyboardButton("9. Tag",      callback_data="ef_9"),
         InlineKeyboardButton("10. Category",callback_data="ef_10")],
        [InlineKeyboardButton("❌ Cancel",   callback_data="cancel")],
    ])

def summary_text(d, category):
    return f"""
📋 **PREVIEW — Confirm karo?**

🎌 **Title:** {d.get('name','')}
📂 **Category:** {category}
🏷️ **Tag:** {d.get('tag','(none)')}
🎭 **Genre:** {d.get('genre','')}
📅 **Year:** {d.get('year','')}
📺 **Seasons:** {d.get('seasons','')}
🎬 **Episodes:** {d.get('episodes','')}
🔗 **Link:** {d.get('tg_link','')}
🖼️ **Image:** {d.get('image_url','')}
📖 **Synopsis:**
{d.get('synopsis','')}
"""

# ══════════════════════════════════════════════════════════════════════════════
#  /start — Welcome message
# ══════════════════════════════════════════════════════════════════════════════
@bot.on_message(filters.command("start"))
async def cmd_start(_, m: Message):
    if not is_admin(m.from_user.id):
        await m.reply(
            "❌ **Access Denied!**\n\n"
            "Ye bot sirf @kenshin_anime ke admin ke liye hai.\n"
            "Channel join karo: https://t.me/kenshin_anime"
        )
        return

    name = m.from_user.first_name or "Admin"
    await m.reply(
        f"👋 **Welcome back, {name}!**\n\n"
        "🎌 **KENSHIN ANIME — Admin Control Panel**\n\n"
        "Is bot se tu poori website control kar sakta hai:\n"
        "• Anime upload karna\n"
        "• Manwha / Movie add karna\n"
        "• Featured, Classic, New section manage karna\n"
        "• Kisi bhi anime ko edit ya delete karna\n"
        "• Website stats dekhna\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 Sab commands dekhne ke liye:\n"
        "👉 /help\n\n"
        "🚀 Abhi kuch add karne ke liye:\n"
        "👉 /upload"
    )

# ══════════════════════════════════════════════════════════════════════════════
#  /help — Full command list with examples
# ══════════════════════════════════════════════════════════════════════════════
@bot.on_message(filters.command("help"))
async def cmd_help(_, m: Message):
    if not is_admin(m.from_user.id):
        await m.reply("❌ Access nahi hai tujhe!")
        return

    # Multiple messages mein bhejo — ek mein sab nahi aata
    await m.reply(
        "📖 **KENSHIN ANIME BOT — HELP MENU**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Sab commands 7 categories mein hain.\n"
        "Neeche detail bhejta hoon 👇"
    )

    await m.reply(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📤 **[1/7] UPLOAD COMMANDS**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "▶️ `/upload`\n"
        "Naya anime step-by-step add karo.\n"
        "Bot puchega: Title → Link → Image → Genre → Synopsis → Seasons → Episodes → Year → Tag\n"
        "Phir category choose karoge (Anime / Featured / Classic / New)\n"
        "✅ Confirm ke baad website pe automatically dikhe ga!\n\n"

        "▶️ `/uploadmanwha`\n"
        "Manwha page pe add karne ke liye.\n"
        "Same step-by-step process — category auto 'manwha' hogi.\n\n"

        "▶️ `/uploadmovie`\n"
        "Movie page pe add karne ke liye.\n"
        "Same process — category auto 'movie' hogi.\n\n"

        "💡 **Tip:** Image URL ke liye Imgur use karo.\n"
        "imgur.com → upload → right click → Copy image address"
    )

    await m.reply(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✏️ **[2/7] EDIT COMMANDS**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "▶️ `/edit`\n"
        "Kisi bhi anime ka koi bhi field edit karo.\n"
        "Bot puchega anime ka naam → phir field choose karne ke liye buttons aayenge:\n"
        "  1. Title  2. TG Link  3. Image\n"
        "  4. Genre  5. Synopsis  6. Seasons\n"
        "  7. Episodes  8. Year  9. Tag  10. Category\n\n"

        "▶️ `/editfeatured`\n"
        "Sirf Featured section ke anime dikhenge — unhe edit karo.\n\n"

        "▶️ `/editclassic`\n"
        "Sirf Classic section ke anime dikhenge — unhe edit karo.\n\n"

        "▶️ `/editnew`\n"
        "Sirf New Releases ke anime dikhenge — unhe edit karo.\n\n"

        "▶️ `/editmanwha`\n"
        "Sirf Manwha page ke items dikhenge — unhe edit karo.\n\n"

        "▶️ `/editmovie`\n"
        "Sirf Movie page ke items dikhenge — unhe edit karo.\n\n"

        "💡 **Tip:** Naam exactly waise likhna jaisa database mein hai.\n"
        "Sahi naam check karne ke liye /list use karo."
    )

    await m.reply(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📂 **[3/7] CATEGORY / MOVE COMMANDS**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "🗂️ **Categories kya hoti hain?**\n"
        "  `anime`    → Main Anime page ka grid\n"
        "  `featured` → Home page ka 'Featured' row\n"
        "  `classic`  → Home page ka 'Classics' row\n"
        "  `new`      → Home page ka 'New Releases' row\n"
        "  `manwha`   → Manwha page\n"
        "  `movie`    → Movies page\n\n"

        "▶️ `/setfeatured`\n"
        "Koi anime ko Home page ke Featured section mein move karo.\n"
        "Example: /setfeatured → bot puchega naam → Solo Leveling\n\n"

        "▶️ `/setclassic`\n"
        "Koi anime ko Classic section mein move karo.\n"
        "Example: /setclassic → Death Note type karo\n\n"

        "▶️ `/setnew`\n"
        "Koi anime ko New Releases section mein move karo.\n\n"

        "▶️ `/moveto`\n"
        "Kisi bhi category mein move karo — buttons se choose karo.\n"
        "Example: /moveto → naam daalo → Manwha / Movie / etc. buttons aayenge"
    )

    await m.reply(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🗑️ **[4/7] DELETE COMMANDS**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "▶️ `/delete`\n"
        "Anime ko PERMANENTLY delete karo database se.\n"
        "⚠️ Ye wapas nahi aayega!\n"
        "Bot puchega: Konsa anime delete karna? → naam type karo\n"
        "Example: `/delete` → Solo Leveling\n\n"

        "▶️ `/hide`\n"
        "Anime ko temporarily HIDE karo.\n"
        "Website pe nahi dikhega, but database mein rahega.\n"
        "Baad mein /unhide se wapas la sakte ho.\n"
        "Example: `/hide` → Gintama\n\n"

        "▶️ `/unhide`\n"
        "Hidden anime ko wapas website pe VISIBLE karo.\n"
        "Example: `/unhide` → Gintama\n\n"

        "💡 **Tip:** Koi anime temporarily hatana ho (maintenance, wrong info)\n"
        "to /hide use karo. Permanent hatana ho to /delete use karo."
    )

    await m.reply(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📋 **[5/7] LIST & VIEW COMMANDS**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "▶️ `/list`\n"
        "Database mein sab anime/manwha/movies ki list dekho.\n"
        "Format: ✅ Naam — [category] TAG\n"
        "Hidden items bhi dikhenge (👁️ se mark hoge)\n\n"

        "▶️ `/listcat <category>`\n"
        "Sirf ek specific category ki list dekho.\n\n"
        "Examples:\n"
        "  `/listcat anime`    → Sirf anime page wale\n"
        "  `/listcat featured` → Sirf featured wale\n"
        "  `/listcat classic`  → Sirf classics\n"
        "  `/listcat new`      → Sirf new releases\n"
        "  `/listcat manwha`   → Sirf manwha\n"
        "  `/listcat movie`    → Sirf movies\n\n"

        "💡 **Tip:** Edit karne se pehle /listcat se exact naam confirm karo."
    )

    await m.reply(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📊 **[6/7] STATS COMMAND**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "▶️ `/stats`\n"
        "Website ki poori stats dekho:\n"
        "  • Total anime count\n"
        "  • Manwha count\n"
        "  • Movies count\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🏷️ **[7/7] TAGS KYA HAIN?**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "Tags anime card pe badge dikhate hain:\n\n"
        "🔴 `HOT`     → Trending anime ke liye\n"
        "🔵 `NEW`     → Naya anime hai\n"
        "🟡 `MUST`    → Must watch recommendation\n"
        "🟣 `TOP`     → Top rated\n"
        "🟠 `CLASSIC` → Old classic anime\n"
        "🟢 `ONGOING` → Abhi chal raha hai\n"
        "⬜ `None`    → Koi badge nahi\n\n"

        "Tag upload ke time bhi set hota hai, ya baad mein:\n"
        "`/edit` → naam daao → Tag option choose karo"
    )

    await m.reply(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ **QUICK REFERENCE — ALL COMMANDS**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📤 **UPLOAD**\n"
        "`/upload` `/uploadmanwha` `/uploadmovie`\n\n"
        "✏️ **EDIT**\n"
        "`/edit` `/editfeatured` `/editclassic`\n"
        "`/editnew` `/editmanwha` `/editmovie`\n\n"
        "📂 **MOVE**\n"
        "`/setfeatured` `/setclassic` `/setnew` `/moveto`\n\n"
        "🗑️ **DELETE**\n"
        "`/delete` `/hide` `/unhide`\n\n"
        "📋 **LIST**\n"
        "`/list` `/listcat` `/stats`\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Koi problem? Claude se pooch! 😄\n"
        "Start karo: 👉 /upload"
    )

# ══════════════════════════════════════════════════════════════════════════════
#  /upload — Step-by-step upload start
# ══════════════════════════════════════════════════════════════════════════════
@bot.on_message(filters.command(["upload","uploadmanwha","uploadmovie"]))
async def cmd_upload(_, m: Message):
    if not is_admin(m.from_user.id): return
    uid = m.from_user.id
    cmd = m.command[0].lower()

    preset_category = {"upload": None, "uploadmanwha": "manwha", "uploadmovie": "movie"}[cmd]

    clear_state(uid)
    data[uid] = {"_preset_cat": preset_category}

    if preset_category:
        states[uid] = "step_0"  # Go to first upload step
        await m.reply(f"📤 **{preset_category.upper()} UPLOAD — Start!**\n\n" + UPLOAD_STEPS[0][1])
    else:
        # Pehle category choose karao
        states[uid] = "choose_cat"
        await m.reply(
            "📂 **Konsi category mein add karna hai?**",
            reply_markup=category_keyboard("upload")
        )

# ─ Category button callback ───────────────────────────────────────────────────
@bot.on_callback_query(filters.regex(r"^cat_(.+)_upload$"))
async def cb_category(_, cb):
    uid = cb.from_user.id
    if not is_admin(uid): return
    cat = cb.matches[0].group(1)
    data[uid]["_preset_cat"] = cat
    states[uid] = "step_0"
    await cb.message.edit(f"✅ Category: **{cat}**\n\n" + UPLOAD_STEPS[0][1])

# ─ Tag button callback ────────────────────────────────────────────────────────
@bot.on_callback_query(filters.regex(r"^tag_(.*)$"))
async def cb_tag(_, cb):
    uid = cb.from_user.id
    if not is_admin(uid): return
    tag = cb.matches[0].group(1)
    data[uid]["tag"] = tag
    states[uid] = "step_8"  # year step
    await cb.message.edit(
        f"✅ Tag: **{tag or 'None'}**\n\n" + UPLOAD_STEPS[7][1]  # year step
    )

# ─ Confirm callback ───────────────────────────────────────────────────────────
@bot.on_callback_query(filters.regex("^confirm_add$"))
async def cb_confirm(_, cb):
    uid = cb.from_user.id
    if not is_admin(uid): return
    d = data.get(uid, {})
    cat = d.get("_preset_cat", "anime")

    payload = {
        "title":    d.get("name", ""),
        "genre":    d.get("genre", ""),
        "tag":      d.get("tag", ""),
        "image_url":d.get("image_url", ""),
        "tg_link":  d.get("tg_link", ""),
        "seasons":  d.get("seasons", "1"),
        "episodes": d.get("episodes", "12"),
        "year":     d.get("year", "2024"),
        "synopsis": d.get("synopsis", ""),
        "category": cat,
        "visible":  True,
    }
    await cb.message.edit("⏳ Adding to database...")
    result = await api_post("/admin/add", payload)
    await cb.message.edit(result.get("msg", "❌ Error"))
    clear_state(uid)

# ─ Cancel callback ────────────────────────────────────────────────────────────
@bot.on_callback_query(filters.regex("^cancel$"))
async def cb_cancel(_, cb):
    uid = cb.from_user.id
    clear_state(uid)
    await cb.message.edit("❌ Cancelled.")

# ── EDIT FIELD CALLBACK ───────────────────────────────────────────────────────
@bot.on_callback_query(filters.regex(r"^ef_(\d+)$"))
async def cb_edit_field(_, cb):
    uid = cb.from_user.id
    if not is_admin(uid): return
    num = cb.matches[0].group(1)
    field_info = EDIT_FIELDS.get(num)
    if not field_info: return
    field, prompt = field_info
    data[uid]["_edit_field"] = field
    states[uid] = "editing_field"
    await cb.message.edit(prompt)

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN MESSAGE HANDLER — State machine
# ══════════════════════════════════════════════════════════════════════════════
@bot.on_message(filters.text & ~filters.command(
    ["start","help","upload","uploadmanwha","uploadmovie",
     "edit","editfeatured","editclassic","editnew","editmanwha","editmovie",
     "delete","hide","unhide","list","listcat","stats","moveto",
     "setfeatured","setclassic","setnew"]
))
async def handle_steps(_, m: Message):
    if not is_admin(m.from_user.id): return
    uid = m.from_user.id
    state = states.get(uid)
    txt = m.text.strip()

    if txt.lower() in ["/cancel", "cancel"]:
        clear_state(uid)
        await m.reply("❌ Cancelled.")
        return

    # ── UPLOAD STEPS ──────────────────────────────────────────────────────────
    if state and state.startswith("step_"):
        step_num = int(state.split("_")[1])
        step_key, _ = UPLOAD_STEPS[step_num]
        data[uid][step_key] = txt

        next_step = step_num + 1

        # After step 7 (year=index 7), ask for tag with buttons
        if step_num == 6:  # episodes done, now year
            states[uid] = f"step_7"
            await m.reply(UPLOAD_STEPS[7][1])

        elif step_num == 7:  # year done, now tag
            states[uid] = "step_tag"
            await m.reply("🏷️ **Step — TAG**\n\nKonsa badge lagana hai?", reply_markup=tag_keyboard())

        elif next_step < len(UPLOAD_STEPS):
            states[uid] = f"step_{next_step}"
            await m.reply(UPLOAD_STEPS[next_step][1])

        # After tag we show confirm (handled by callback)
        return

    # After tag callback sets step_8 (year), let message handler grab year
    if state == "step_8":
        data[uid]["year"] = txt
        states[uid] = "step_tag"
        await m.reply("🏷️ **Tag choose karo:**", reply_markup=tag_keyboard())
        return

    # ── EDIT FIELD VALUE ──────────────────────────────────────────────────────
    if state == "editing_field":
        field = data[uid].get("_edit_field")
        title = data[uid].get("_edit_title", "")
        if not field or not title:
            await m.reply("❌ Error. /edit se dobara shuru karo.")
            clear_state(uid)
            return
        msg = await m.reply("⏳ Updating...")
        result = await api_patch(f"/admin/edit/{title}", {"field": field, "value": txt})
        await msg.edit(result.get("msg", "❌ Error") + "\n\n✏️ Aur koi field edit karna?\n/edit se karo.")
        clear_state(uid)
        return

    # ── WAITING FOR TITLE (for edit/delete/etc) ───────────────────────────────
    if state == "wait_edit_title":
        data[uid]["_edit_title"] = txt
        states[uid] = "editing_field_choose"
        await m.reply(
            f"📝 Editing: **{txt}**\n\nKonsa field edit karna hai?",
            reply_markup=edit_field_keyboard()
        )
        return

    if state == "wait_delete_title":
        msg = await m.reply(f"⏳ Deleting '{txt}'...")
        result = await api_delete(f"/admin/delete/{txt}")
        await msg.edit(result.get("msg","❌ Error"))
        clear_state(uid)
        return

    if state == "wait_hide_title":
        result = await api_patch(f"/admin/hide/{txt}")
        await m.reply(result.get("msg","❌ Error"))
        clear_state(uid)
        return

    if state == "wait_unhide_title":
        result = await api_patch(f"/admin/show/{txt}")
        await m.reply(result.get("msg","❌ Error"))
        clear_state(uid)
        return

    if state == "wait_moveto_title":
        data[uid]["_move_title"] = txt
        states[uid] = "wait_moveto_cat"
        await m.reply(
            f"📂 '{txt}' ko kahan move karna hai?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ Featured",   callback_data=f"moveto_featured_{txt}")],
                [InlineKeyboardButton("👑 Classic",    callback_data=f"moveto_classic_{txt}")],
                [InlineKeyboardButton("🆕 New Release",callback_data=f"moveto_new_{txt}")],
                [InlineKeyboardButton("🎌 Anime",      callback_data=f"moveto_anime_{txt}")],
                [InlineKeyboardButton("📖 Manwha",     callback_data=f"moveto_manwha_{txt}")],
                [InlineKeyboardButton("🎬 Movie",      callback_data=f"moveto_movie_{txt}")],
                [InlineKeyboardButton("❌ Cancel",     callback_data="cancel")],
            ])
        )
        return

# ─ Move category callback ─────────────────────────────────────────────────────
@bot.on_callback_query(filters.regex(r"^moveto_(\w+)_(.+)$"))
async def cb_moveto(_, cb):
    uid = cb.from_user.id
    if not is_admin(uid): return
    cat   = cb.matches[0].group(1)
    title = cb.matches[0].group(2)
    await cb.message.edit("⏳ Moving...")
    result = await api_patch(f"/admin/move/{title}?category={cat}", {})
    await cb.message.edit(result.get("msg","❌ Error"))
    clear_state(uid)

# ── EDIT COMMANDS ──────────────────────────────────────────────────────────────
async def start_edit(m: Message, filter_cat: str = None):
    uid = m.from_user.id
    if not is_admin(uid): return
    clear_state(uid)

    if filter_cat:
        # Show list of anime in that category
        items = await api_get(f"/anime/category/{filter_cat}")
        if not items:
            await m.reply(f"📭 {filter_cat} mein koi anime nahi hai!")
            return
        text = f"✏️ **{filter_cat.upper()} ANIME — Konsa edit karna?**\n\nTitle exactly likhna:\n\n"
        for i in items:
            text += f"• `{i['title']}`\n"
        await m.reply(text)
    else:
        await m.reply("✏️ **EDIT**\n\nKis anime ka naam hai? (Exactly likhna)")

    states[uid] = "wait_edit_title"
    data[uid] = {"_filter_cat": filter_cat}

@bot.on_message(filters.command("edit"))
async def cmd_edit(_, m): await start_edit(m)

@bot.on_message(filters.command("editfeatured"))
async def cmd_edit_feat(_, m): await start_edit(m, "featured")

@bot.on_message(filters.command("editclassic"))
async def cmd_edit_class(_, m): await start_edit(m, "classic")

@bot.on_message(filters.command("editnew"))
async def cmd_edit_new(_, m): await start_edit(m, "new")

@bot.on_message(filters.command("editmanwha"))
async def cmd_edit_manwha(_, m): await start_edit(m, "manwha")

@bot.on_message(filters.command("editmovie"))
async def cmd_edit_movie(_, m): await start_edit(m, "movie")

# ── MOVE SHORTCUTS ─────────────────────────────────────────────────────────────
@bot.on_message(filters.command(["moveto","setfeatured","setclassic","setnew"]))
async def cmd_move(_, m: Message):
    uid = m.from_user.id
    if not is_admin(uid): return
    cmd = m.command[0].lower()
    quick = {"setfeatured":"featured","setclassic":"classic","setnew":"new"}
    if cmd in quick:
        data[uid] = {"_quick_cat": quick[cmd]}
        states[uid] = "wait_moveto_title"
        await m.reply(f"📝 Konsa anime {quick[cmd]} mein move karna?\n\nTitle likhna:")
    else:
        clear_state(uid)
        states[uid] = "wait_moveto_title"
        data[uid] = {}
        await m.reply("📝 Konsa anime move karna?\n\nTitle likhna:")

# ── DELETE ─────────────────────────────────────────────────────────────────────
@bot.on_message(filters.command("delete"))
async def cmd_delete(_, m: Message):
    uid = m.from_user.id
    if not is_admin(uid): return
    clear_state(uid)
    states[uid] = "wait_delete_title"
    await m.reply("🗑️ **DELETE**\n\nKis anime ka naam hai? (Exactly likhna)\n\n⚠️ Ye permanently delete hoga!")

@bot.on_message(filters.command("hide"))
async def cmd_hide(_, m: Message):
    uid = m.from_user.id
    if not is_admin(uid): return
    clear_state(uid)
    states[uid] = "wait_hide_title"
    await m.reply("👁️ **HIDE**\n\nKonsa anime hide karna? (Title exactly likhna)")

@bot.on_message(filters.command("unhide"))
async def cmd_unhide(_, m: Message):
    uid = m.from_user.id
    if not is_admin(uid): return
    clear_state(uid)
    states[uid] = "wait_unhide_title"
    await m.reply("✅ **UNHIDE**\n\nKonsa anime wapas visible karna?")

# ── LIST / STATS ───────────────────────────────────────────────────────────────
@bot.on_message(filters.command("list"))
async def cmd_list(_, m: Message):
    if not is_admin(m.from_user.id): return
    msg = await m.reply("⏳ Fetching list...")
    items = await api_get("/admin/list")
    if not items:
        await msg.edit("📭 Database empty hai!")
        return
    text = f"📋 **ALL ANIME ({len(items)} total)**\n\n"
    for i in items:
        vis = "✅" if i.get("visible") else "👁️ hidden"
        text += f"{vis} `{i['title']}` — [{i.get('category','anime')}] {i.get('tag','')}\n"
    # Split agar lamba ho
    if len(text) > 4000:
        chunks = [text[i:i+4000] for i in range(0,len(text),4000)]
        await msg.edit(chunks[0])
        for c in chunks[1:]: await m.reply(c)
    else:
        await msg.edit(text)

@bot.on_message(filters.command("listcat"))
async def cmd_listcat(_, m: Message):
    if not is_admin(m.from_user.id): return
    if len(m.command) < 2:
        await m.reply("Format: `/listcat featured`\nOptions: `anime` `featured` `classic` `new` `manwha` `movie`")
        return
    cat = m.command[1].lower()
    items = await api_get(f"/anime/category/{cat}")
    if not items:
        await m.reply(f"📭 {cat} mein kuch nahi!")
        return
    text = f"📋 **{cat.upper()} ({len(items)})**\n\n"
    for i in items:
        text += f"• `{i['title']}` {i.get('tag','')}\n"
    await m.reply(text)

@bot.on_message(filters.command("stats"))
async def cmd_stats(_, m: Message):
    if not is_admin(m.from_user.id): return
    d = await api_get("/stats")
    await m.reply(f"""
📊 **KENSHIN ANIME STATS**

🎌 Total Titles: **{d.get('total',0)}**
📖 Manwha: **{d.get('manwha',0)}**
🎬 Movies: **{d.get('movies',0)}**

🌐 Website live hai!
""")

# ── HANDLE TAG STEP (after year, before confirm) ─────────────────────────────
# state = "step_tag" is handled by tag_keyboard callback above
# After tag is picked, show confirm
@bot.on_callback_query(filters.regex(r"^tag_(.*)$"))
async def cb_tag_confirm(_, cb):
    uid = cb.from_user.id
    if not is_admin(uid): return
    tag = cb.matches[0].group(1)
    data[uid]["tag"] = tag
    # Show summary + confirm
    cat = data[uid].get("_preset_cat","anime")
    summary = summary_text(data[uid], cat)
    await cb.message.edit(summary, reply_markup=confirm_keyboard())
    states[uid] = "confirming"

# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🤖 Kenshin Admin Bot starting...")
    bot.run()
