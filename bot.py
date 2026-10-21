
import os
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
PROMO_CODE = "redaalilivea"
BONUS = 1_000_000
DB = "points.db"

conn = sqlite3.connect(DB)
conn.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER NOT NULL DEFAULT 0
)
""")
conn.execute("""
CREATE TABLE IF NOT EXISTS used_codes (
    user_id INTEGER,
    code TEXT,
    PRIMARY KEY (user_id, code)
)
""")
conn.commit()


def add_user(user_id):
    conn.execute(
        "INSERT OR IGNORE INTO users(user_id) VALUES (?)",
        (user_id,)
    )
    conn.commit()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user(update.effective_user.id)
    keyboard = [
        ["🎟️ كود النقاط", "💰 نقاطي"],
    ]
    await update.message.reply_text(
        "أهلاً بك في بوت التمويل ⭐\n"
        "اجمع النقاط واستعمل كود المكافأة!",
        reply_markup=ReplyKeyboardMarkup(
            keyboard, resize_keyboard=True
        ),
    )


async def handle_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    add_user(user_id)

    if text == "💰 نقاطي":
        row = conn.execute(
            "SELECT points FROM users WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        await update.message.reply_text(
            f"رصيدك الحالي: {row[0]:,} نقطة ⭐"
        )
        return

    if text == "🎟️ كود النقاط":
        context.user_data["waiting_for_code"] = True
        await update.message.reply_text("أرسل كود النقاط:")
        return

    if context.user_data.get("waiting_for_code"):
        context.user_data["waiting_for_code"] = False
        code = text.lower()

        if code != PROMO_CODE:
            await update.message.reply_text("❌ الكود غير صحيح.")
            return

        try:
            conn.execute(
                "INSERT INTO used_codes(user_id, code) VALUES (?, ?)",
                (user_id, PROMO_CODE)
            )
            conn.execute(
                "UPDATE users SET points = points + ? WHERE user_id = ?",
                (BONUS, user_id)
            )
            conn.commit()
            await update.message.reply_text(
                "🎉 مبروك! حصلت على مليون نقطة ⭐"
            )
        except sqlite3.IntegrityError:
            conn.rollback()
            await update.message.reply_text(
                "❌ سبق واستخدمت هذا الكود."
            )
        return

    await update.message.reply_text(
        "اختار زر من القائمة حتى تتابع."
    )


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN غير مضبوط في إعدادات الاستضافة")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    app.run_polling()


if __name__ == "__main__":
    main()

