from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
from datetime import datetime import os

TOKEN = os.getenv('TOKEN')
CHANNEL_ID = '-1002566593151'
FORCE_JOIN_CHANNEL = '@Moadelnahaye'

SELECT_MAJOR, ASK_SCORE = range(2)

majors = {
    "🎓 تجربی": {
        "دینی": 4.78,
        "عربی": 2.62,
        "فارسی": 5.95,
        "زیست": 6.39,
        "زبان": 3.32,
        "شیمی": 5.27
    },
    "📐 ریاضی": {
        "دینی": 4.78,
        "عربی": 2.62,
        "فارسی": 5.95,
        "هندسه": 5.10,
        "زبان": 3.32,
        "فیزیک": 6.57
    }
}

# بررسی عضویت در کانال
async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        member = await context.bot.get_chat_member(FORCE_JOIN_CHANNEL, user.id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_membership(update, context):
        await update.message.reply_text(
            f"📢 برای استفاده از ربات، ابتدا در کانال زیر عضو شوید:\n{FORCE_JOIN_CHANNEL}"
        )
        return ConversationHandler.END

    # پاک‌سازی اطلاعات قبلی کاربر برای ثبت مجدد
    context.user_data.clear()

    keyboard = [["🎓 تجربی", "📐 ریاضی"]]
    await update.message.reply_text(
        "لطفاً رشته تحصیلی خود را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return SELECT_MAJOR

async def select_major(update: Update, context: ContextTypes.DEFAULT_TYPE):
    major = update.message.text
    if major not in majors:
        await update.message.reply_text("❌ لطفاً یکی از رشته‌های موجود را انتخاب کنید.")
        return SELECT_MAJOR

    context.user_data["major"] = major
    context.user_data["scores"] = {}
    context.user_data["subjects"] = list(majors[major].keys())
    context.user_data["current"] = 0

    subject = context.user_data["subjects"][0]
    await update.message.reply_text(f"✏️ نمره درس {subject} را وارد کنید (بین ۰ تا ۲۰):")
    return ASK_SCORE

async def ask_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        score = float(update.message.text.replace(',', '.'))
        if not (0 <= score <= 20):
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ لطفاً نمره‌ای معتبر بین ۰ تا ۲۰ وارد کنید.")
        return ASK_SCORE

    subjects = context.user_data["subjects"]
    current = context.user_data["current"]
    subject = subjects[current]
    context.user_data["scores"][subject] = score
    context.user_data["current"] += 1

    if context.user_data["current"] >= len(subjects):
        # محاسبه معدل
        total_weighted = 0
        total_credits = 0
        for s, score in context.user_data["scores"].items():
            z = majors[context.user_data["major"]][s]
            total_weighted += score * z
            total_credits += z
        avg = round(total_weighted / total_credits, 2)

                # ارسال به کانال
        user_id = update.effective_user.id
        user_name = update.effective_user.username
        full_name = update.effective_user.full_name
        today = datetime.now().strftime("%Y-%m-%d")

        message = "📊 کارنامه جدید ثبت شد:\n"
        if user_name:
            message += f"یوزرنیم: @{user_name}\n"
        message += f"نام: {full_name}\n"
        message += f"آیدی: `{user_id}`\n"

        for s, score in context.user_data["scores"].items():
            message += f"{s} : {score}\n"
        message += f"📈 میانگین: {avg}\n🗓 تاریخ: {today}"

        await context.bot.send_message(chat_id=CHANNEL_ID, text=message)
        await update.message.reply_text(f"✅ معدل کل شما: {avg}\n\nبرای ثبت کارنامه جدید، دوباره /start را بزنید.")
        return ConversationHandler.END

    # پرسیدن نمره بعدی
    next_subject = subjects[context.user_data["current"]]
    await update.message.reply_text(f"✏️ نمره درس {next_subject} را وارد کنید (بین ۰ تا ۲۰):")
    return ASK_SCORE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⛔ عملیات لغو شد. برای شروع دوباره /start را بفرستید.")
    return ConversationHandler.END

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_MAJOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_major)],
            ASK_SCORE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_score)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)
    print("ربات اجرا شد...")
    app.run_polling()
