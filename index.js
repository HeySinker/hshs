const express = require("express");
const fetch = require("node-fetch");

const app = express();
app.use(express.json());

const TELEGRAM_TOKEN = process.env.TELEGRAM_TOKEN;
const GITHUB_TOKEN = process.env.BITHUB_TOKEN;
const REPO = "HeySinker/bsbs";
const FILE_PATH = "config.json";
const BRANCH = "main";

const GITHUB_API_URL = `https://api.github.com/repos/${REPO}/contents/${FILE_PATH}`;

// دالة لتحديث config.json على GitHub
async function updatePassOnGitHub(newPass) {
  const headers = { 
    "Authorization": `token ${GITHUB_TOKEN}`,
    "Accept": "application/vnd.github.v3+json"
  };

  // جلب الملف الحالي
  const r = await fetch(GITHUB_API_URL, { headers });
  const data = await r.json();
  const sha = data.sha;

  const contentUrl = data.download_url;
  const contentRes = await fetch(contentUrl);
  const config = await contentRes.json();

  // تعديل القيمة المطلوبة
  config.pools[0].pass = newPass;

  // رفع الملف المعدل
  const body = {
    message: `Telegram-bot update: set pass -> ${newPass}`,
    content: Buffer.from(JSON.stringify(config, null, 2)).toString("base64"),
    sha: sha,
    branch: BRANCH
  };

  const putRes = await fetch(GITHUB_API_URL, {
    method: "PUT",
    headers: headers,
    body: JSON.stringify(body)
  });
  return putRes.ok;
}

// استقبال Webhook من Telegram
app.post("/webhook", async (req, res) => {
  const update = req.body;
  if (update.message && update.message.text) {
    const chat_id = update.message.chat.id;
    const text = update.message.text.trim();

    const success = await updatePassOnGitHub(text);
    const reply = success ? 
      `تم تحديث pass إلى: ${text}` :
      "فشل التحديث!";

    await fetch(`https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat_id, text: reply })
    });
  }
  res.send({ ok: true });
});

// تشغيل السيرفر على Vercel
app.listen(process.env.PORT || 3000, () => {
  console.log("Server running...");
});

module.exports = app; // مطلوب لـ Vercel
