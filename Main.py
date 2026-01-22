# main.py
import sqlite3, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# === CONFIG ===
TOKEN = "8305677367:AAGjr1Z6w6lVMpLJwCILmYrMrjs8hSyUJ8o"

# === DATABASE ===
db = sqlite3.connect("solo_leveling.db", check_same_thread=False)
cursor = db.cursor()

# === TABLES ===
cursor.execute("""
CREATE TABLE IF NOT EXISTS players(
    id INTEGER PRIMARY KEY,
    name TEXT,
    level INTEGER,
    hp INTEGER,
    exp INTEGER,
    gold INTEGER,
    guild TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS guilds(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    leader_id INTEGER,
    members TEXT
)
""")
db.commit()

# === GIFS LOCAUX ===
gifs = {
    "start": "gifs/main.gif",
    "hunt": ["gifs/hunt1.gif", "gifs/hunt2.gif", "gifs/hunt3.gif"],
    "level_up": "gifs/level_up.gif"
}

# === SHOP ITEMS ===
shop_items = {
    "Potion de soin": 50,
    "Épée de fer": 200,
    "Armure légère": 150
}

# === UTILS ===
def level_up(player):
    new_level = player[2]
    new_exp = player[4]
    new_hp = player[3]
    level_up_text = ""
    if new_exp >= 100:
        new_level += 1
        new_exp -= 100
        new_hp = 100
        level_up_text = "🎉 Tu as monté de niveau!"
    return new_level, new_exp, new_hp, level_up_text

# === COMMANDES ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cursor.execute("SELECT * FROM players WHERE id=?", (user.id,))
    player = cursor.fetchone()
    if not player:
        cursor.execute(
            "INSERT INTO players (id, name, level, hp, exp, gold, guild) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user.id, user.first_name, 1, 100, 0, 0, "")
        )
        db.commit()
        await update.message.reply_animation(open(gifs["start"], "rb"), caption=f"Bienvenue {user.first_name}! L'aventure Solo Leveling commence.")
    else:
        await update.message.reply_text(f"Re-bienvenue {user.first_name}! Tape /menu pour voir les commandes.")

# === Profile ===
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cursor.execute("SELECT * FROM players WHERE id=?", (user.id,))
    player = cursor.fetchone()
    if player:
        text = (
            f"Profil de {player[1]}:\n"
            f"Niveau: {player[2]}\n"
            f"HP: {player[3]}\n"
            f"EXP: {player[4]}/100\n"
            f"Gold: {player[5]}\n"
            f"Guilde: {player[6] if player[6] else 'Aucune'}"
        )
        await update.message.reply_text(text)
    else:
        await update.message.reply_text("Tu n'as pas encore commencé. Tape /start")

# === Hunt ===
async def hunt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cursor.execute("SELECT * FROM players WHERE id=?", (user.id,))
    player = cursor.fetchone()
    if not player:
        await update.message.reply_text("Commence d'abord l'aventure avec /start")
        return

    enemy_level = random.randint(player[2], player[2]+2)
    damage = random.randint(10, 30)
    exp_gain = random.randint(5, 20)
    gold_gain = random.randint(10, 50)

    new_hp = player[3] - damage
    new_exp = player[4] + exp_gain
    new_gold = player[5] + gold_gain
    new_level, new_exp, new_hp, level_up_text = level_up(player)

    cursor.execute(
        "UPDATE players SET level=?, hp=?, exp=?, gold=? WHERE id=?",
        (new_level, new_hp, new_exp, new_gold, user.id)
    )
    db.commit()

    hunt_gif = random.choice(gifs["hunt"])
    text = (
        f"Tu as combattu un ennemi de niveau {enemy_level}!\n"
        f"Dégâts subis: {damage}\n"
        f"EXP gagné: {exp_gain} | Gold gagné: {gold_gain}\n"
        f"{level_up_text}\n"
        f"HP: {new_hp} | Niveau: {new_level} | EXP: {new_exp}/100 | Gold: {new_gold}"
    )
    await update.message.reply_animation(open(hunt_gif, "rb"), caption=text)

# === Donjon ===
async def donjon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cursor.execute("SELECT * FROM players WHERE id=?", (user.id,))
    player = cursor.fetchone()
    if not player:
        await update.message.reply_text("Commence d'abord avec /start")
        return

    stages = random.randint(3, 5)
    total_damage = total_exp = total_gold = 0
    for _ in range(stages):
        damage = random.randint(5, 20)
        exp_gain = random.randint(5, 15)
        gold_gain = random.randint(10, 30)
        total_damage += damage
        total_exp += exp_gain
        total_gold += gold_gain

    new_hp = max(player[3] - total_damage, 0)
    new_exp = player[4] + total_exp
    new_gold = player[5] + total_gold
    new_level, new_exp, new_hp, level_up_text = level_up(player)

    cursor.execute(
        "UPDATE players SET level=?, hp=?, exp=?, gold=? WHERE id=?",
        (new_level, new_hp, new_exp, new_gold, user.id)
    )
    db.commit()

    donjon_gif = random.choice(gifs["hunt"])
    text = (
        f"Tu as traversé {stages} étages du donjon!\n"
        f"Dégâts subis: {total_damage}\n"
        f"EXP gagné: {total_exp} | Gold gagné: {total_gold}\n"
        f"{level_up_text}\n"
        f"HP: {new_hp} | Niveau: {new_level} | EXP: {new_exp}/100 | Gold: {new_gold}"
    )
    await update.message.reply_animation(open(donjon_gif, "rb"), caption=text)

# === Shop ===
async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cursor.execute("SELECT * FROM players WHERE id=?", (user.id,))
    player = cursor.fetchone()
    if not player:
        await update.message.reply_text("Commence d'abord avec /start")
        return

    keyboard = [[InlineKeyboardButton(f"{item} - {price}G", callback_data=f"buy_{item}")] for item, price in shop_items.items()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"💰 Shop | Ton Gold: {player[5]}", reply_markup=reply_markup)

async def shop_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    cursor.execute("SELECT * FROM players WHERE id=?", (user.id,))
    player = cursor.fetchone()
    if not player:
        await query.edit_message_text("Commence d'abord avec /start")
        return

    data = query.data
    if data.startswith("buy_"):
        item_name = data[4:]
        price = shop_items[item_name]
        if player[5] >= price:
            new_gold = player[5] - price
            cursor.execute("UPDATE players SET gold=? WHERE id=?", (new_gold, user.id))
            db.commit()
            await query.edit_message_text(f"✅ Tu as acheté {item_name}! Gold restant: {new_gold}")
        else:
            await query.edit_message_text("❌ Gold insuffisant!")

# === Daily (récompense journalière) ===
async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    gold_bonus = random.randint(50, 150)
    cursor.execute("UPDATE players SET gold = gold + ? WHERE id=?", (gold_bonus, user.id))
    db.commit()
    await update.message.reply_text(f"💰 Daily: Tu as reçu {gold_bonus} Gold!")

# === Menu principal ===
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Hunt", callback_data="hunt"), InlineKeyboardButton("Donjon", callback_data="donjon")],
        [InlineKeyboardButton("Ombres", callback_data="ombres"), InlineKeyboardButton("Shop", callback_data="shop")],
        [InlineKeyboardButton("Profile", callback_data="profile"), InlineKeyboardButton("Daily", callback_data="daily")],
        [InlineKeyboardButton("Guilde", callback_data="guilde"), InlineKeyboardButton("Raid", callback_data="raid")],
        [InlineKeyboardButton("Prestige", callback_data="prestige"), InlineKeyboardButton("Top", callback_data="top")],
        [InlineKeyboardButton("Boss Mondial", callback_data="boss"), InlineKeyboardButton("Guild War", callback_data="guild_war")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📜 Menu Principal", reply_markup=reply_markup)

# === Button handler ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "hunt":
        await hunt(update, context)
    elif data == "donjon":
        await donjon(update, context)
    elif data == "shop":
        await shop(update, context)
    elif data.startswith("buy_"):
        await shop_button(update, context)
    elif data == "profile":
        await profile(update, context)
    elif data == "daily":
        await daily(update, context)
    else:
        await query.edit_message_text(f"Commande {data} à implémenter…")

# === Reset ===
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cursor.execute("DELETE FROM players WHERE id=?", (user.id,))
    db.commit()
    await update.message.reply_text("Ton aventure a été réinitialisée. Tape /start pour recommencer.")

# === MAIN ===
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("profile", profile))
app.add_handler(CommandHandler("hunt", hunt))
app.add_handler(CommandHandler("donjon", donjon))
app.add_handler(CommandHandler("shop", shop))
app.add_handler(CommandHandler("daily", daily))
app.add_handler(CommandHandler("menu", menu))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(CallbackQueryHandler(button_handler))

print("Bot is running...")
app.run_polling()
