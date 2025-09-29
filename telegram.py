# requirements:
# pip install python-telegram-bot==13.15 requests

import os, base64, json, requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# -------------------- التكوين --------------------
# يمكنك وضع القيم هنا مباشرة لو تحب، لكن أفضل عبر env vars:
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN") or "<8366143899:AAEqMzlFhaxP3bJ-tVudeDwugIHGqkhnKtw>"
GITHUB_TOKEN   = os.environ.get("GITHUB_TOKEN")   or "<SHA256:h+L7wPhLnxFY2NjpA3pTv1N4yawM8G6W6dGH1OY6U5Y>"

GITHUB_OWNER = "HeySinker"
GITHUB_REPO  = "fsfs"
FILE_PATH    = "config.json"
BRANCH       = "main"

# قائمة القيم الممكنة لحقل "pass"
PASS_LIST = [
    "NX1",
    "NX2",
    "Ze",
    "HM"
]

GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{FILE_PATH}"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# -------------------- وظائف GitHub --------------------
def get_file_from_github():
    r = requests.get(GITHUB_API_URL, headers=HEADERS, params={"ref": BRANCH})
    r.raise_for_status()
    return r.json()

def update_file_on_github(new_bytes, sha, commit_msg):
    content_b64 = base64.b64encode(new_bytes).decode("utf-8")
    payload = {
        "message": commit_msg,
        "content": content_b64,
        "sha": sha,
        "branch": BRANCH
    }
    r = requests.put(GITHUB_API_URL, headers=HEADERS, json=payload)
    r.raise_for_status()
    return r.json()

def set_pass_in_json(target_value):
    filedata = get_file_from_github()
    sha = filedata["sha"]
    content_b64 = filedata["content"]
    raw = base64.b64decode(content_b64)
    cfg = json.loads(raw)

    modified = False
    for pool in cfg.get("pools", []):
        # نطابق على coin+url للتأكد أننا نغيّر الحقل الصحيح
        if pool.get("coin") == "XMR" and pool.get("url") == "pool.supportxmr.com:443":
            pool["pass"] = target_value
            modified = True
            break

    if not modified:
        raise RuntimeError("لم أجد مدخل pool المطلوب للتعديل.")

    new_raw = json.dumps(cfg, indent=2).encode("utf-8")
    commit_msg = f"Telegram-bot update: set pass -> {target_value}"
    return update_file_on_github(new_raw, sha, commit_msg)

# -------------------- أوامر تيليجرام --------------------
def start(update: Update, context: CallbackContext):
    update.message.reply_text("بوت مستعد. استخدم /listpasses لعرض الخيارات و /setpass <index> للتعيين.")

def listpasses(update: Update, context: CallbackContext):
    lines = [f"{i}: {v}" for i, v in enumerate(PASS_LIST)]
    update.message.reply_text("قائمة القيم المتاحة:\n" + "\n".join(lines))

def setpass_cmd(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("استخدم: /setpass <index>")
        return
    try:
        idx = int(context.args[0])
        value = PASS_LIST[idx]
    except Exception:
        update.message.reply_text("فهرس غير صالح. استخدم /listpasses لعرض الفهارس.")
        return

    update.message.reply_text(f"جاري تحديث 'pass' إلى: {value} ...")
    try:
        res = set_pass_in_json(value)
        commit_sha = res.get("commit", {}).get("sha", "unknown")
        update.message.reply_text(f"تم التحديث بنجاح. Commit SHA: {commit_sha}")
    except Exception as e:
        update.message.reply_text(f"فشل التحديث: {e}")

# -------------------- تشغيل البوت --------------------
def main():
    if not TELEGRAM_TOKEN or not GITHUB_TOKEN:
        print("تحذير: TELEGRAM_TOKEN أو GITHUB_TOKEN غير موجودين. ضعهم في متغيرات البيئة أو مباشرة في الكود.")
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("listpasses", listpasses))
    dp.add_handler(CommandHandler("setpass", setpass_cmd, pass_args=True))
    print("Bot started. Polling...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
