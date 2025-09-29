# requirements:
# pip install python-telegram-bot==13.15 requests

import sys
import types

# Patch لموديول imghdr غير موجود في Python 3.13
sys.modules['imghdr'] = types.ModuleType('imghdr')

import os
import base64
import json
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# ---------- Configuration (put secrets in env vars) ----------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GITHUB_TOKEN   = os.environ.get("BITHUB_TOKEN")  # كما هو
GITHUB_OWNER   = "HeySinker"
GITHUB_REPO    = "fsfs"
FILE_PATH      = "config.json"
BRANCH         = "main"

PASS_LIST = [
    "NX",
    "NX2",
    "NX3",
    "NX4",
    "ZE",
    "HM",
    # ... أضف ما تريد
]

GITHUB_API_BASE = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{FILE_PATH}"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# ---------- Helper functions ----------
def get_file_from_github():
    params = {"ref": BRANCH}
    r = requests.get(GITHUB_API_BASE, headers=HEADERS, params=params)
    r.raise_for_status()
    return r.json()

def update_file_on_github(new_content_bytes, sha, commit_message):
    content_b64 = base64.b64encode(new_content_bytes).decode("utf-8")
    payload = {
        "message": commit_message,
        "content": content_b64,
        "sha": sha,
        "branch": BRANCH
    }
    r = requests.put(GITHUB_API_BASE, headers=HEADERS, json=payload)
    r.raise_for_status()
    return r.json()

def set_pass_in_json(target_pass_value):
    data = get_file_from_github()
    sha = data["sha"]
    content_b64 = data["content"]
    raw = base64.b64decode(content_b64)
    config = json.loads(raw)

    modified = False
    for pool in config.get("pools", []):
        if pool.get("coin") == "XMR" and pool.get("url") == "pool.supportxmr.com:443":
            pool["pass"] = target_pass_value
            modified = True
            break

    if not modified:
        raise RuntimeError("Couldn't find the target pool to modify.")

    new_raw = json.dumps(config, indent=2).encode("utf-8")
    commit_msg = f"Telegram-bot: update pool pass -> {target_pass_value}"
    return update_file_on_github(new_raw, sha, commit_msg)

# ---------- Telegram command handlers ----------
def start(update: Update, context: CallbackContext):
    update.message.reply_text("بوت GitHub ready. استخدم /setpass <index> لتعيين قيمة من القائمة.")

def list_passes(update: Update, context: CallbackContext):
    text = "قائمة القيم المتاحة:\n" + "\n".join(f"{i}: {v}" for i, v in enumerate(PASS_LIST))
    update.message.reply_text(text)

def setpass_cmd(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("استخدم: /setpass <index>")
        return
    try:
        idx = int(context.args[0])
        value = PASS_LIST[idx]
    except Exception:
        update.message.reply_text("فهرس غير صالح. استخدم /listpasses لمشاهدة الفهارس.")
        return

    update.message.reply_text(f"جاري تحديث القيمة إلى: {value} ...")
    try:
        res = set_pass_in_json(value)
        commit_sha = res.get("commit", {}).get("sha", "unknown")
        update.message.reply_text(f"تم التحديث بنجاح. Commit: {commit_sha}")
    except Exception as e:
        update.message.reply_text(f"فشل التحديث: {e}")

# ---------- Main ----------
def main():
    if not TELEGRAM_TOKEN or not GITHUB_TOKEN:
        raise SystemExit("تأكد من وجود TELEGRAM_TOKEN وBITHUB_TOKEN في متغيرات البيئة.")
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("listpasses", list_passes))
    dp.add_handler(CommandHandler("setpass", setpass_cmd, pass_args=True))
    print("Bot started")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
