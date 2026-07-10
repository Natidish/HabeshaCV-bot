# -*- coding: utf-8 -*-
"""
app.py
Render ላይ "Web Service" (free tier) ተብሎ ለማሰማራት የተዘጋጀ entry point።

ለምን ይህ ፋይል ያስፈልጋል?
--------------------
Render የ "Web Service" free tier ብቻ ነፃ ስለሆነ (Background Worker ክፍያ ስለሚጠይቅ)፣
ነገር ግን Web Service የግድ በ $PORT ላይ HTTP ጥያቄዎችን መመለስ አለበት፣ አለበለዚያ Render
service ጤናማ አይደለም ብሎ ደጋግሞ ያጠፋዋል/ያስነሳዋል (restart loop)።

ስለዚህ እዚህ ፋይል ውስጥ፦
 1. ትንሽ Flask web server በ $PORT ላይ እናስነሳለን (Render የሚፈልገውን HTTP ፍላጎት ያሟላል)
 2. የ Telegram bot ን (polling mode) በ background thread ውስጥ እናስኬደዋለን

⚠️ አስፈላጊ ማስታወሻ፦ Render free tier services ለ 15 ደቂቃ ያለ traffic ከቆዩ
"ይተኛሉ" (spin down)። bot ይህ ሲሆን ከ Telegram ጋር ያለው ግንኙነት ይቋረጣል። ይህንን
ለመከላከል፣ እንደ UptimeRobot ወይም cron-job.org የመሳሰሉ ነፃ አገልግሎቶችን ተጠቅመው
ይህን URL በየ 5-10 ደቂቃው በ HTTP GET እንዲጎበኙት ማድረግ ይመከራል፦
    https://<your-service-name>.onrender.com/
"""

import os
import threading
import logging

from flask import Flask

import bot  # bot.py ውስጥ ያለው build_application()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

flask_app = Flask(__name__)


@flask_app.route("/")
def health_check():
    """Render ይህን URL በ HTTP GET እየደጋገመ በመጎብኘት service እንደ 'up' ይቆጥረዋል።"""
    return "✅ CV Maker Telegram Bot is running.", 200


def run_bot_polling():
    """የ Telegram bot ን በ polling mode በ background thread ውስጥ ያስኬዳል።"""
    application = bot.build_application()
    logger.info("Bot polling started in background thread...")
    # stop_signals=None: ምክንያቱም signal handlers ማዘጋጀት የሚቻለው
    # main thread ላይ ብቻ ስለሆነ (እዚህ ግን background thread ውስጥ ነን)።
    application.run_polling(
        allowed_updates=bot.Update.ALL_TYPES,
        stop_signals=None,
        close_loop=False,
    )


def start_bot_thread():
    thread = threading.Thread(target=run_bot_polling, daemon=True)
    thread.start()
    logger.info("Background bot thread started.")


# Render/gunicorn ፋይሉን import ሲያደርጉ bot thread ወዲያውኑ ይጀምራል
start_bot_thread()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)
