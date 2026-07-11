
"""
bot.py
CV Maker Telegram Bot
----------------------
ፍሰት:
 1. ተጠቃሚ /start ይላካል
 2. Bot እያንዳንዱን የ CV መረጃ በተራ ይጠይቃል (ስም, ስልክ, ኢሜይል, አድራሻ, ማጠቃለያ,
    የስራ ልምድ, ትምህርት, ችሎታ, ቋንቋ)
 3. ተጠቃሚው ካረጋገጠ በኋላ Bot ፕሮፌሽናል PDF ይሰራል እና በ password ይቆልፈዋል
 4. የተቆለፈውን PDF ለተጠቃሚው ይልካል + "ክፍያ ይፈጸሙ" የሚል መልእክት ከ 2 አማራጭ ጋር
    (Telegram Stars ወይም Teleberr)
 5. ክፍያው ከተረጋገጠ በኋላ password ወደ ተጠቃሚው ይላካል
"""
 
import asyncio
import logging
import os
 
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    filters,
)
 
import config
from cv_pdf import generate_locked_cv
 
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
 
# ---------------------------------------------------------------------------
# Conversation states
# ---------------------------------------------------------------------------
(
    FULL_NAME, PHONE, EMAIL, ADDRESS, SUMMARY,
    EXPERIENCE, EDUCATION, SKILLS, LANGUAGES, CONFIRM,
) = range(10)
 
# in-memory store: {user_id: {"password":..., "locked_pdf":..., "paid": bool}}
PENDING = {}
 
 
# ---------------------------------------------------------------------------
# Helper keyboards
# ---------------------------------------------------------------------------
def confirm_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ ትክክል ነው፣ CV ስራልኝ", callback_data="confirm_yes")],
        [InlineKeyboardButton("🔁 እንደገና ልጀምር", callback_data="confirm_restart")],
    ])
 
 
def payment_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🌟 በ Telegram Stars ክፈል ({config.STAR_PRICE}⭐)",
                               callback_data="pay_stars")],
        [InlineKeyboardButton("💵 በ Teleberr ክፈል", callback_data="pay_teleberr")],
    ])
 
 
# ---------------------------------------------------------------------------
# Conversation: collecting CV data
# ---------------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "👋 እንኳን ደህና መጡ!\n\n"
        "ይህ Bot ፕሮፌሽናል CV በ PDF ቅርጸት ሰርቶ የሚሰጥዎ ነው።\n"
        f"💰 ዋጋ፡ {config.PRICE_BIRR} ብር ብቻ።\n\n"
        "እስቲ እንጀምር። የ *ሙሉ ስምዎ* ይላኩልኝ፦",
        parse_mode=ParseMode.MARKDOWN,
    )
    return FULL_NAME
 
 
async def get_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["full_name"] = update.message.text.strip()
    await update.message.reply_text("📞 የስልክ ቁጥርዎን ይላኩ፦")
    return PHONE
 
 
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text.strip()
    await update.message.reply_text("📧 ኢሜይል አድራሻዎን ይላኩ (ከሌለዎት 'የለኝም' ይላኩ)፦")
    return EMAIL
 
 
async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["email"] = "" if text in ("የለኝም", "-", "የለም") else text
    await update.message.reply_text("📍 አድራሻዎን ይላኩ (ከተማ/ክልል)፦")
    return ADDRESS
 
 
async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["address"] = update.message.text.strip()
    await update.message.reply_text(
        "📝 ስለ እርስዎ አጭር ማጠቃለያ (professional summary) ይላኩ፦\n"
        "ምሳሌ፡ 'የ3 ዓመት ልምድ ያለው ሶፍትዌር ዲቨሎፐር...'"
    )
    return SUMMARY
 
 
async def get_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["summary"] = update.message.text.strip()
    await update.message.reply_text(
        "💼 የስራ ልምድዎን ይላኩ።\n\n"
        "እያንዳንዱን ልምድ በዚህ ቅርጸት፣ በአዲስ መስመር ይጻፉ፦\n"
        "`የስራ ድርሻ | ድርጅት | ጊዜ | አጭር መግለጫ`\n\n"
        "ምሳሌ፦\n"
        "`ሶፍትዌር ዲቨሎፐር | ABC ኩባንያ | 2022 - አሁን | ድረ-ገጾችን መስራት`\n\n"
        "ካልኖረዎት 'የለኝም' ብለው ይላኩ።",
        parse_mode=ParseMode.MARKDOWN,
    )
    return EXPERIENCE
 
 
async def get_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["experience"] = "" if text in ("የለኝም", "-") else text
    await update.message.reply_text(
        "🎓 የትምህርት ደረጃዎን ይላኩ።\n\n"
        "ቅርጸት፦ `ደረጃ | ትምህርት ቤት/ዩኒቨርሲቲ | ዓመት`\n"
        "ምሳሌ፦ `BSc Computer Science | አዲስ አበባ ዩኒቨርሲቲ | 2020`\n\n"
        "ከአንድ በላይ ካለ በአዲስ መስመር ይጻፉ።",
        parse_mode=ParseMode.MARKDOWN,
    )
    return EDUCATION
 
 
async def get_education(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["education"] = update.message.text.strip()
    await update.message.reply_text(
        "🛠 ችሎታዎችዎን (skills) በኮማ (,) ተለያይተው ይላኩ፦\n"
        "ምሳሌ፦ Python, JavaScript, Communication, Team work"
    )
    return SKILLS
 
 
async def get_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["skills"] = update.message.text.strip()
    await update.message.reply_text(
        "🗣 የሚናገሯቸውን ቋንቋዎች በኮማ (,) ተለያይተው ይላኩ፦\n"
        "ምሳሌ፦ አማርኛ, English"
    )
    return LANGUAGES
 
 
async def get_languages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["languages"] = update.message.text.strip()
 
    data = context.user_data
    preview = (
        "📋 *የገባው መረጃ ይህ ነው፤ እባክዎ ያረጋግጡ፦*\n\n"
        f"👤 ስም፡ {data.get('full_name')}\n"
        f"📞 ስልክ፡ {data.get('phone')}\n"
        f"📧 ኢሜይል፡ {data.get('email') or '-'}\n"
        f"📍 አድራሻ፡ {data.get('address')}\n"
        f"📝 ማጠቃለያ፡ {data.get('summary')}\n"
        f"💼 ልምድ፡ {data.get('experience') or '-'}\n"
        f"🎓 ትምህርት፡ {data.get('education')}\n"
        f"🛠 ችሎታ፡ {data.get('skills')}\n"
        f"🗣 ቋንቋ፡ {data.get('languages')}\n"
    )
    await update.message.reply_text(
        preview, parse_mode=ParseMode.MARKDOWN, reply_markup=confirm_keyboard()
    )
    return CONFIRM
 
 
async def confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
 
    if query.data == "confirm_restart":
        context.user_data.clear()
        await query.edit_message_text("🔁 እሺ፣ ከመጀመሪያው እንጀምር። /start ብለው ይላኩ።")
        return ConversationHandler.END
 
    # confirm_yes -> generate the PDF
    await query.edit_message_text("⏳ CV እየተሰራ ነው፣ እባክዎ ይጠብቁ...")
 
    user_id = query.from_user.id
    data = context.user_data
 
    locked_pdf_path, password = generate_locked_cv(data, config.WORK_DIR, user_id)
 
    PENDING[user_id] = {
        "password": password,
        "locked_pdf": locked_pdf_path,
        "paid": False,
        "full_name": data.get("full_name", ""),
    }
 
    with open(locked_pdf_path, "rb") as f:
        await context.bot.send_document(
            chat_id=user_id,
            document=f,
            filename="CV.pdf",
            caption=(
                "✅ CV ዎ ተዘጋጅቷል!\n\n"
                "🔒 ይህ PDF በ *password* የተቆለፈ ነው። ለመክፈት password ያስፈልጋል።\n"
                f"💰 password ለማግኘት {config.PRICE_BIRR} ብር መክፈል አለብዎት።\n\n"
                "እባክዎ ከታች ካሉት አማራጮች አንዱን በመጫን ይክፈሉ 👇"
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
 
    await context.bot.send_message(
        chat_id=user_id,
        text="💳 *የክፍያ አማራጮች*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=payment_keyboard(),
    )
 
    return ConversationHandler.END
 
 
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ ተሰርዟል። እንደገና ለመጀመር /start ይላኩ።")
    return ConversationHandler.END
 
 
# ---------------------------------------------------------------------------
# Payment: Telegram Stars
# ---------------------------------------------------------------------------
async def pay_with_stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
 
    if user_id not in PENDING:
        await query.message.reply_text("⚠️ መጀመሪያ CV ይስሩ፣ /start ይላኩ።")
        return
 
    prices = [LabeledPrice("CV PDF Password", config.STAR_PRICE)]
 
    await context.bot.send_invoice(
        chat_id=user_id,
        title="የ CV PDF Password",
        description=f"የ CV PDF ን ለመክፈት የሚያስፈልግ password ({config.PRICE_BIRR} ብር ተመጣጣኝ)።",
        payload=f"cv_password_{user_id}",
        provider_token="",  # ለ Telegram Stars ባዶ ይሆናል
        currency="XTR",
        prices=prices,
    )
 
 
async def pre_checkout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    # እዚህ ላይ ተጨማሪ ማረጋገጫ ማድረግ ይቻላል
    await query.answer(ok=True)
 
 
async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
 
    if user_id not in PENDING:
        await update.message.reply_text(
            "✅ ክፍያዎ ተቀብለናል፣ ነገር ግን የ CV መረጃ አላገኘንም። እባክዎ /start ብለው ይላኩ።"
        )
        return
 
    PENDING[user_id]["paid"] = True
    password = PENDING[user_id]["password"]
 
    await update.message.reply_text(
        "✅ ክፍያዎ በተሳካ ሁኔታ ተጠናቅቋል!\n\n"
        f"🔑 የ CV PDF ዎን password፦\n`{password}`\n\n"
        "ይህን password በ PDF ሲከፍቱ ይጠቀሙ። አመሰግናለሁ! 🙏",
        parse_mode=ParseMode.MARKDOWN,
    )
 
 
# ---------------------------------------------------------------------------
# Payment: Teleberr (manual verification by admin)
# ---------------------------------------------------------------------------
async def pay_with_teleberr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
 
    if user_id not in PENDING:
        await query.message.reply_text("⚠️ መጀመሪያ CV ይስሩ፣ /start ይላኩ።")
        return
 
    await context.bot.send_message(
        chat_id=user_id,
        text=(
            "💵 *Teleberr ክፍያ መመሪያ*\n\n"
            f"1️⃣ {config.PRICE_BIRR} ብር ወደሚከተለው Teleberr አካውንት ይላኩ፦\n"
            f"👤 ስም፡ *{config.TELEBERR_ACCOUNT_NAME}*\n"
            f"📱 ቁጥር፡ `{config.TELEBERR_ACCOUNT_NUMBER}`\n\n"
            "2️⃣ ክፍያውን ከጨረሱ በኋላ የክፍያ ማረጋገጫ *screenshot* (ፎቶ) እዚሁ ቻት ላይ ይላኩልኝ።\n\n"
            "3️⃣ ካረጋገጥን በኋላ password ወዲያውኑ ይላክልዎታል።"
        ),
        parse_mode=ParseMode.MARKDOWN,
    )
 
 
async def receive_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ተጠቃሚው የ Teleberr screenshot ሲልክ admin ጋር ይደርሳል።"""
    user = update.message.from_user
    user_id = user.id
 
    if user_id not in PENDING:
        return  # ተጠቃሚው CV ገና አልሰራም፤ ፎቶውን ችላ እንል
 
    if PENDING[user_id].get("paid"):
        await update.message.reply_text("✅ ክፍያዎ ቀደም ብሎ ተረጋግጧል።")
        return
 
    photo = update.message.photo[-1]
 
    caption = (
        "🧾 *አዲስ የ Teleberr ክፍያ ማረጋገጫ*\n\n"
        f"👤 ስም፡ {user.full_name}\n"
        f"🆔 User ID፡ `{user_id}`\n"
        f"📄 CV ስም፡ {PENDING[user_id].get('full_name')}\n\n"
        "ክፍያውን አረጋግጠው password ለመላክ ከታች ይምረጡ 👇"
    )
 
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ አረጋግጥ (Approve)", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton("❌ አትቀበል (Reject)", callback_data=f"reject_{user_id}"),
        ]
    ])
 
    await context.bot.send_photo(
        chat_id=config.ADMIN_CHAT_ID,
        photo=photo.file_id,
        caption=caption,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard,
    )
 
    await update.message.reply_text(
        "📨 የክፍያ ማረጋገጫዎ ለ አስተዳዳሪ ተልኳል። እባክዎ ይጠብቁ፣ በቅርቡ password ይደርስዎታል።"
    )
 
 
async def admin_decision_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin ብቻ 'Approve'/'Reject' ሲጫን የሚሰራ handler።"""
    query = update.callback_query
 
    if query.from_user.id != config.ADMIN_CHAT_ID:
        await query.answer("⛔ ይህን የመጫን ፍቃድ የለዎትም።", show_alert=True)
        return
 
    await query.answer()
    action, user_id_str = query.data.split("_", 1)
    user_id = int(user_id_str)
 
    if user_id not in PENDING:
        await query.edit_message_caption(caption="⚠️ ይህ ተጠቃሚ ውሂብ አልተገኘም (ምናልባት expired)።")
        return
 
    if action == "approve":
        PENDING[user_id]["paid"] = True
        password = PENDING[user_id]["password"]
 
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "✅ ክፍያዎ ተረጋግጧል! አመሰግናለሁ።\n\n"
                f"🔑 የ CV PDF password፦\n`{password}`\n\n"
                "ይህን password በ PDF ሲከፍቱ ይጠቀሙ።"
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n✅ *ጸድቋል፣ password ተልኳል*",
            parse_mode=ParseMode.MARKDOWN,
        )
 
    elif action == "reject":
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "❌ የላኩት የክፍያ ማረጋገጫ ትክክል ሆኖ አልተገኘም።\n"
                "እባክዎ ትክክለኛ screenshot ወይም ትክክለኛ መጠን መላክዎን ያረጋግጡ እና እንደገና ይላኩ።"
            ),
        )
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n❌ *ውድቅ ተደርጓል*",
            parse_mode=ParseMode.MARKDOWN,
        )
 
 
# ---------------------------------------------------------------------------
# Build the Application (used both for local polling and for Render deploy)
# ---------------------------------------------------------------------------
def build_application() -> Application:
    if config.BOT_TOKEN == "PUT_YOUR_BOT_TOKEN_HERE":
        raise SystemExit(
            "እባክዎ config.py ላይ ወይም .env ፋይል ውስጥ BOT_TOKEN ያስቀምጡ።"
        )
 
    os.makedirs(config.WORK_DIR, exist_ok=True)
 
    application = Application.builder().token(config.BOT_TOKEN).build()
 
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_full_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            SUMMARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_summary)],
            EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_experience)],
            EDUCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_education)],
            SKILLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_skills)],
            LANGUAGES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_languages)],
            CONFIRM: [CallbackQueryHandler(confirm_callback, pattern="^confirm_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
 
    application.add_handler(conv_handler)
 
    # Payment button handlers
    application.add_handler(CallbackQueryHandler(pay_with_stars, pattern="^pay_stars$"))
    application.add_handler(CallbackQueryHandler(pay_with_teleberr, pattern="^pay_teleberr$"))
 
    # Telegram Stars payment handlers
    application.add_handler(PreCheckoutQueryHandler(pre_checkout_callback))
    application.add_handler(
        MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback)
    )
 
    # Teleberr manual flow
    application.add_handler(MessageHandler(filters.PHOTO, receive_payment_proof))
    application.add_handler(
        CallbackQueryHandler(admin_decision_callback, pattern="^(approve|reject)_")
    )
 
    return application
 
 
def main():
    """በራስ ኮምፒዩተር ላይ (locally) ለ testing ብቻ ጥቅም ላይ የሚውል - polling mode."""
    # አዲስ የ Python ስሪቶች (3.14+) ላይ asyncio.get_event_loop() ራሱ አዲስ
    # event loop መፍጠር ስለሚያቆም፣ ራሳችን በግልጽ loop እንፈጥራለን/እናዘጋጃለን።
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
 
    application = build_application()
    logger.info("Bot is starting (polling mode)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
 
 
if __name__ == "__main__":
    main()
 
