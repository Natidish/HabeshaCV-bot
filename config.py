# -*- coding: utf-8 -*-
"""
config.py
የ bot ማስተካከያዎች (settings). እነዚህን በ environment variable ወይም
በ .env ፋይል ውስጥ ማስቀመጥ ይመከራል (ደህንነት ስለሆነ)።
"""

import os
from dotenv import load_dotenv

load_dotenv()  # .env ፋይል ካለ ይጫናል

# ============ አስፈላጊ ማስተካከያዎች (ከ BotFather / environment ይምጡ) ============

# ከ @BotFather ያገኙት bot token
BOT_TOKEN = os.getenv("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")

# የእርስዎ (የአስተዳዳሪ/admin) Telegram chat id።
# ይህ ቁጥር ለ Teleberr ክፍያ ማረጋገጫ ማሳወቂያ የሚላክበት ነው።
# ቁጥሩን ለማወቅ @userinfobot ን ያናግሩ።
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "123456789"))

# ============ ክፍያ ማስተካከያዎች ============

PRICE_BIRR = 200  # የCV ዋጋ በብር

# Telegram Stars ዋጋ (Telegram Stars ውስጥ ብቻ ጥቅም ላይ የሚውል integer ቁጥር ነው)።
# 1 Star ≈ ስንት ብር እንደሆነ Telegram ራሱ ይወስናል፤ ስለዚህ ይህን ቁጥር እርስዎ
# ካሁኑ የ Star ዋጋ ተመን ጋር እያመሳከሩ ያስተካክሉት።
STAR_PRICE = int(os.getenv("STAR_PRICE", "100"))

# Teleberr የክፍያ መረጃ (ራስዎ የቴሌብር አካውንት ይተኩ)
TELEBERR_ACCOUNT_NAME = os.getenv("TELEBERR_ACCOUNT_NAME", "Your Full Name")
TELEBERR_ACCOUNT_NUMBER = os.getenv("TELEBERR_ACCOUNT_NUMBER", "09XXXXXXXX")

# ============ ፋይል ማስቀመጫ ============
WORK_DIR = os.getenv("WORK_DIR", "cv_files")
