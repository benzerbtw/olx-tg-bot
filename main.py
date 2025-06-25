import requests
from bs4 import BeautifulSoup
import os
from flask import Flask

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 🔍 Твои поисковые фильтры
SEARCH_TARGETS = [
    ("iphone 12", 50000, 100000),
    ("айфон 12", 50000, 100000),
    ("айфон 13", 50000, 130000),
    ("айфон 12 про", 50000, 110000),
    ("айфон 12 про макс", 50000, 110000),
    ("айфон 13 про макс", 50000, 160000),
    ("iphone 12 pro max", 50000, 110000),
    ("iphone 13 pro max", 50000, 160000),
    ("айфон 13 про", 50000, 150000),
    ("iphone 12 pro", 50000, 110000),
    ("iphone 13", 50000, 130000),
    ("iphone 13 pro", 50000, 150000),
    ("iphone 14", 50000, 170000),
]

BLACKLIST_KEYWORDS = ["копия", "реплика"]
HEADERS = {"User-Agent": "Mozilla/5.0"}
SENT_FILE = "sent.txt"

def load_sent_links():
    return set(open(SENT_FILE).read().splitlines()) if os.path.exists(SENT_FILE) else set()

def save_sent_link(link):
    with open(SENT_FILE, "a") as f:
        f.write(link + "\n")

def send_photo(photo_url, caption):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
        data={"chat_id": CHAT_ID, "photo": photo_url, "caption": caption, "parse_mode": "HTML"}
    )

def send_telegram(message):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    )

def check_ads():
    sent_links = load_sent_links()
    for keyword, min_price, max_price in SEARCH_TARGETS:
        url = f"https://www.olx.kz/elektronika/astana/?search[dist]=30&search[order]=created_at:desc&q={keyword.replace(' ', '%20')}"

        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")

        ads = soup.select("div[data-cy='l-card']")[:10]
        for ad in ads:
            link_tag = ad.find("a", href=True)
            title_tag = ad.find("h6") or ad.find("h4")
            price_tag = ad.find("p", class_="css-uj7mm0") or ad.find("h3")
            img_tag = ad.find("img")

            if not (link_tag and title_tag and price_tag):
                continue

            title = title_tag.text.strip().lower()
            if any(bad in title for bad in BLACKLIST_KEYWORDS):
                continue

            price_text = price_tag.text.strip().replace("₸", "").replace(" ", "").replace("\xa0", "")
            try:
                price = int(''.join(filter(str.isdigit, price_text)))
            except ValueError:
                continue

            if not (min_price <= price <= max_price):
                continue

            link = "https://www.olx.kz" + link_tag["href"]
            if link in sent_links:
                continue

            caption = (
                f"📱 <b>{title_tag.text.strip()}</b>\n"
                f"💰 <b>{price} ₸</b>\n"
                f"🔍 Поиск: <i>{keyword}</i>\n"
                f"🔗 <a href='{link}'>Смотреть объявление</a>"
            )

            if img_tag and img_tag.get("src"):
                send_photo(img_tag["src"], caption)
            else:
                send_telegram(caption)

            save_sent_link(link)
            print("✅ Отправлено:", title_tag.text.strip())

# Flask сервер
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ OLX бот работает!"

@app.route("/run")
def run_bot():
    send_telegram("🤖 Бот начал проверку объявлений!")
    check_ads()
    return "🔁 Проверка завершена!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
def check_ads():
    try:
        sent_links = load_sent_links()
        # ... весь остальной код
    except Exception as e:
        print("Ошибка при проверке объявлений:", e)
        send_telegram(f"❌ Ошибка: {e}")
