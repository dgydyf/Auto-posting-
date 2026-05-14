import os, json, threading
from datetime import datetime
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# ========== CONFIG ==========
ADMIN_IDS = [8508012498, 8225821294]
BOT_PASSWORD = "1910398591@#aA"
# ============================

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Running"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# Database Functions
db_file = "data.json"

def load_db():
    if os.path.exists(db_file):
        with open(db_file, 'r') as f:
            return json.load(f)
    return {"groups": [], "members": [], "states": {}}

def save_db(data):
    with open(db_file, 'w') as f:
        json.dump(data, f, indent=2)

def is_admin(uid):
    return uid in ADMIN_IDS

def is_auth(uid):
    return is_admin(uid) or uid in load_db()["members"]

def get_list():
    db = load_db()
    if not db["groups"]:
        return "No groups added yet."
    text = ""
    for i, g in enumerate(db["groups"], 1):
        link = g.get("link", f"@{g.get('username', 'Private')}")
        text += f"{i}. {g['title']} - {link}\n"
    return text

# ========== COMMANDS ==========
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "😎 Boss! Send the post you want to share. Within a minute, I will forward your message to all groups/channels where I am admin. 😻\n\n"
        "If you don't know the bot's admin or password, you cannot get access. Contact admin ✆@A15287"
    )

async def lst(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_auth(update.effective_user.id):
        await update.message.reply_text("Access Denied")
        return
    await update.message.reply_text(get_list())

async def post_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_auth(update.effective_user.id):
        await update.message.reply_text("Access Denied")
        return
    await update.message.reply_text("😻 Boss! Share what you want to post 😎")
    return 1

async def recv_post(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["msg"] = update.message
    await update.message.reply_text(f"Select channels/groups to post:\n\n{get_list()}\nSend numbers like 1,2,3 or 'All'")
    return 2

async def send_post(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    sel = update.message.text.strip()
    db = load_db()
    groups = db["groups"]
    msg = ctx.user_data.get("msg")
    
    if sel.lower() == "all":
        selected = groups
    else:
        try:
            nums = [int(x.strip()) for x in sel.split(",")]
            selected = [groups[n-1] for n in nums if 1 <= n <= len(groups)]
        except:
            await update.message.reply_text("Invalid. Use 1,2,3 or All")
            return 2
    
    ok, fail = 0, 0
    for g in selected:
        try:
            await msg.copy(chat_id=g["chat_id"])
            ok += 1
        except:
            fail += 1
    
    await update.message.reply_text(f"TOTAL: {len(selected)}\nSuccess: {ok}\nFail: {fail}")
    return ConversationHandler.END

async def add_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_admin(uid):
        await update.message.reply_text("Boss! Submit Telegram ID")
        return 3
    else:
        await update.message.reply_text("😎 Boss! Submit password ✅")
        return 1

async def add_pwd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.text.strip() == BOT_PASSWORD:
        await update.message.reply_text("Boss! Submit Telegram ID")
        return 3
    else:
        await update.message.reply_text("Password incorrect ❌")
        return ConversationHandler.END

async def add_id(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        new_id = int(update.message.text.strip())
        db = load_db()
        if new_id not in db["members"]:
            db["members"].append(new_id)
            save_db(db)
        await update.message.reply_text(f"Member {new_id} added ✅")
    except:
        await update.message.reply_text("Invalid ID")
    return ConversationHandler.END

async def ban_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_admin(uid):
        await update.message.reply_text("Submit Telegram ID")
        return 4
    else:
        await update.message.reply_text("😎 Boss! Submit password ✅")
        return 2

async def ban_pwd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.text.strip() == BOT_PASSWORD:
        await update.message.reply_text("Submit Telegram ID")
        return 4
    else:
        await update.message.reply_text("Password incorrect ❌")
        return ConversationHandler.END

async def ban_id(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ban_id = int(update.message.text.strip())
        if ban_id in ADMIN_IDS:
            await update.message.reply_text("Can't ban admin")
        else:
            db = load_db()
            if ban_id in db["members"]:
                db["members"].remove(ban_id)
                save_db(db)
            await update.message.reply_text(f"Removed {ban_id} ❌")
    except:
        await update.message.reply_text("Invalid ID")
    return ConversationHandler.END

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

async def new_chat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    for m in update.message.new_chat_members:
        if m.id == ctx.bot.id:
            chat = update.effective_chat
            db = load_db()
            link = None
            try:
                inv = await chat.create_invite_link()
                link = inv.invite_link
            except:
                pass
            db["groups"].append({
                "chat_id": chat.id,
                "title": chat.title,
                "username": chat.username,
                "link": link
            })
            save_db(db)

# ========== MAIN ==========
def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("BOT_TOKEN not set!")
        return
    
    threading.Thread(target=run_web, daemon=True).start()
    
    app_bot = Application.builder().token(TOKEN).build()
    
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("list", lst))
    
    app_bot.add_handler(ConversationHandler(
        entry_points=[CommandHandler("post", post_cmd)],
        states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_post)],
                2: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_post)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    ))
    
    app_bot.add_handler(ConversationHandler(
        entry_points=[CommandHandler("add", add_cmd)],
        states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_pwd)],
                3: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_id)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    ))
    
    app_bot.add_handler(ConversationHandler(
        entry_points=[CommandHandler("ban", ban_cmd)],
        states={2: [MessageHandler(filters.TEXT & ~filters.COMMAND, ban_pwd)],
                4: [MessageHandler(filters.TEXT & ~filters.COMMAND, ban_id)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    ))
    
    app_bot.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_chat))
    
    print("Bot Running...")
    app_bot.run_polling()

if __name__ == "__main__":
    main()
