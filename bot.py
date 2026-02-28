#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import re
import json
import logging
from datetime import datetime
import pytz

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ================= CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CAMP_NAME = "KOSALA CAMP"
WORKBOOK_NAME = "C-Mind-User"
SHEET_NAME = "DRILL_DATA"

AUTHORIZED_GROUP_ID = int(os.getenv("AUTHORIZED_GROUP_ID"))
GOOGLE_CREDS = os.getenv("GOOGLE_CREDENTIALS")

TIMEZONE = pytz.timezone("Asia/Kolkata")

# ================= GOOGLE AUTH =================

def get_sheet():
    creds_dict = json.loads(GOOGLE_CREDS)

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    return client.open(WORKBOOK_NAME).worksheet(SHEET_NAME)

sheet = get_sheet()

# ================= AUTH CHECK =================

def is_authorized(chat_id):
    return chat_id == AUTHORIZED_GROUP_ID

# ================= START COMMAND =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Rig Bot Active.\nUse /r to get template.")

# ================= /r TEMPLATE =================

async def send_template(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_authorized(update.effective_chat.id):
        await update.message.reply_text("❌ Unauthorized Group")
        return

    today = datetime.now(TIMEZONE).strftime("%d-%m-%Y")

    template = f"""
{CAMP_NAME}
DATE: {today}

RIG:
1ST SHIFT:
2ND SHIFT:
DEPTH:
1ST SHIFT REMARKS:
2ND SHIFT REMARKS:

RIG:
1ST SHIFT:
2ND SHIFT:
DEPTH:
1ST SHIFT REMARKS:
2ND SHIFT REMARKS:

DAY TOTAL:
"""

    await update.message.reply_text(template.strip())

# ================= SAVE DATA (MULTI RIG) =================

async def save_data(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_authorized(update.effective_chat.id):
        return

    text = update.message.text

    if "RIG:" not in text:
        return

    try:
        date_match = re.search(r"DATE:\s*(.*)", text)
        date = date_match.group(1).strip() if date_match else ""

        rig_blocks = text.split("RIG:")
        saved_count = 0

        for block in rig_blocks[1:]:
            rig_line = block.strip().split("\n")[0].strip()

            s1 = re.search(r"1ST SHIFT:\s*(.*)", block)
            s2 = re.search(r"2ND SHIFT:\s*(.*)", block)
            depth = re.search(r"DEPTH:\s*(.*)", block)
            r1 = re.search(r"1ST SHIFT REMARKS:\s*(.*)", block)
            r2 = re.search(r"2ND SHIFT REMARKS:\s*(.*)", block)

            sheet.append_row([
                CAMP_NAME,
                date,
                rig_line,
                float(s1.group(1)) if s1 and s1.group(1) else "",
                float(s2.group(1)) if s2 and s2.group(1) else "",
                depth.group(1) if depth else "",
                r1.group(1) if r1 else "",
                r2.group(1) if r2 else ""
            ])

            saved_count += 1

        await update.message.reply_text(f"✅ Saved {saved_count} rig entries.")

    except Exception as e:
        await update.message.reply_text("⚠️ Format Error. Use /r template.")

# ================= ERROR HANDLER =================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"Error: {context.error}")

# ================= MAIN =================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("r", send_template))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_data))
    app.add_error_handler(error_handler)

    print("🚀 Rig Bot Running...")
    app.run_polling()