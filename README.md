# CV Maker Telegram Bot

ተጠቃሚው CV information በተራ ሲሰጥ ፕሮፌሽናል PDF CV የሚሰራ፣ በ password የሚቆልፍ፣
እና ክፍያ (Telegram Stars ወይም Teleberr) ከተፈጸመ በኋላ password የሚልክ bot።

## ፋይሎች
- `bot.py` — ዋናው bot ኮድ (conversation flow, payment, admin approval)
- `cv_pdf.py` — CV ን ወደ PDF የሚቀይር + password የሚያደርግ ሞጁል
- `config.py` — ማስተካከያዎች (token, admin id, ዋጋ, Teleberr መረጃ)
- `.env.example` — የ environment variables ምሳሌ
- `requirements.txt` — የሚያስፈልጉ Python packages

## እንዴት ማዘጋጀት (Setup)

### 1. Dependencies መጫን
```bash
pip install -r requirements.txt
```

### 2. Bot Token ማግኘት
1. በ Telegram ላይ [@BotFather](https://t.me/BotFather) ን ያናግሩ
2. `/newbot` ብለው bot ይፍጠሩ እና ያገኙትን **token** ይቅዱ

### 3. የ Admin Chat ID ማግኘት
1. [@userinfobot](https://t.me/userinfobot) ን ያናግሩ፣ የ chat ID ቁጥርዎን ይሰጥዎታል

### 4. `.env` ፋይል ማዘጋጀት
`.env.example` ን ኮፒ አድርገው `.env` ብለው ይሰይሙት፣ ከዛ የራስዎን መረጃ ይሙሉ፦
```bash
cp .env.example .env
```
```env
BOT_TOKEN=እርስዎ ካገኙት BotFather token
ADMIN_CHAT_ID=የእርስዎ chat id
STAR_PRICE=100
TELEBERR_ACCOUNT_NAME=የእርስዎ ስም
TELEBERR_ACCOUNT_NUMBER=የ Teleberr ስልክ ቁጥር
```

### 5. Telegram Stars ማንቃት (አማራጭ)
Telegram Stars ገንዘብ በራስ-ሰር (automatically) ስለሚሰራ ተጨማሪ ማዋቀር አያስፈልገውም -
ቦቱ ካለበት አገር Stars ድጋፍ ካለው በራሱ ይሰራል። **STAR_PRICE** ን ግን ከ200 ብር ጋር
ተመጣጣኝ እንዲሆን እርስዎ ማስተካከል አለብዎት (የ Star ተመን ስለሚቀያየር)።

### 6. Bot ማስኬድ
```bash
python3 bot.py
```

## የ Bot ፍሰት (Flow)

1. **`/start`** → Bot እያንዳንዱን CV መረጃ (ስም, ስልክ, ኢሜይል, አድራሻ, ማጠቃለያ,
   የስራ ልምድ, ትምህርት, ችሎታ, ቋንቋ) በተራ ይጠይቃል
2. ተጠቃሚው ገብቷቸውን መረጃ ካረጋገጠ በኋላ Bot ፕሮፌሽናል PDF ይሰራል
3. PDF በ **ራንደም ቁጥር password** ይቆለፋል
4. የተቆለፈው PDF ለተጠቃሚው ይላካል + "ክፍያ ይፈጽሙ" መልእክት ከ2 አማራጭ ጋር፦
   - 🌟 **Telegram Stars** — ራስ-ሰር (bot ራሱ password ይልካል)
   - 💵 **Teleberr** — ተጠቃሚው ገንዘብ ልኮ screenshot ይልካል → Admin ላይ
     ማረጋገጫ ይደርሳል → Admin "Approve" ሲጫን password ወደ ተጠቃሚ ይላካል

## ማስተካከያ / ማሻሻያ ሃሳቦች (ለ Production)

ይህ ኮድ ለመሰረታዊ አጠቃቀም ዝግጁ ነው፣ ነገር ግን ለትልቅ አገልግሎት ተጨማሪ ማሻሻያ ይመከራል፦

- **Database መጠቀም** (እንደ SQLite/PostgreSQL) — አሁን `PENDING` dict
  in-memory ስለሆነ bot ሲዘጋ/ሲወድቅ መረጃው ይጠፋል
- **PDF ፋይሎችን በየጊዜው ማጽዳት** (`cv_files/` directory ውስጥ የቆዩ ፋይሎችን መሰረዝ)
- **Rate limiting** — አንድ ተጠቃሚ ተደጋጋሚ CV እንዳይሰራ መገደብ
- **Logging ወደ ፋይል** ማድረግ ለ debugging እና ለክፍያ ማረጋገጫ ማህደር (record)
- STAR_PRICE ን ከ Telegram Stars ትክክለኛ ተመን ጋር በየጊዜው ማዘመን
