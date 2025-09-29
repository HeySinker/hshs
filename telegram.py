import os
import json
import requests
from flask import Flask, request

TOKEN = os.getenv("TELEGRAM_TOKEN")
GITHUB_TOKEN = os.getenv("BITHUB_TOKEN")
REPO = "HeySinker/bsbs"
FILE_PATH = "config.json"
BRANCH = "main"

app = Flask(__name__)

# دالة لتحديث config.json على GitHub
def update_json(new_pass_value):
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    # جلب الملف الحالي
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    data = r.json()
    sha = data["sha"]

    content = requests.get(data["download_url"]).json()
    content["pools"][0]["pass"] = new_pass_value

    # رفع الملف المعدل
    update_data = {
        "message": f"update pass to {new_pass_value}",
        "content": json.dumps(content, indent=2).encode("utf-8").decode("utf-8"),
        "sha": sha,
        "branch": BRANCH
    }
    r = requests.put(url, headers=headers, data=json.dumps(update_data))
    return r.status_code == 200 or r.status_code == 201


# استقبال رسائل التلغرام
@app.route(f"/webhook", methods=["POST"])
def webhook():
    update = request.get_json()
    if "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"]["text"].strip()

        # نجرب نحدث القيمة
        if update_json(text):
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={
                "chat_id": chat_id,
                "text": f"تم تحديث pass إلى: {text}"
            })
        else:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={
                "chat_id": chat_id,
                "text": "فشل التحديث!"
            })
    return {"ok": True}
