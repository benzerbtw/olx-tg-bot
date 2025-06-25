import requests
from bs4 import BeautifulSoup
import os
from flask import Flask

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SEARCH_TARGETS = [
    ("iphone 12", 50000, 90000 ),
    ("айфон 12", 50000, 90000),
    ("айфон 13", 50000, 130000),
    ("айфон 12 про", 50000, 100000),
    ("айфон 12 про макс", 50000, 110000),
    ("айфон 13 про макс", 50000, 170000),
    ("iphone 12 pro max", 50000, 110000),
    ("iphone 13 pro max", 50000, 170000),
    ("айфон 13 про", 50000, 150000),
    ("iphone 12 pro", 50000, 100000),
    ("iphone 13", 50000, 130000),
    ("iphone 13 pro", 50000, 150000),
    ("iphone 14", 50000, 170000),
]

BLACKLIST_KEYWORDS = [
    "копия", "реплика"
]

HEADERS = {"User-Agent": "Mozilla/5.0"}
SENT_FILE = "sent.txt"


def load_sent_links():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            return set(f.read().splitlines())
    return set()


def save_sent_link(link):
    with open(SENT_FILE, "a") as f:
        f.write(link + "\n")


def send_photo(photo_url, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    data = {
        "chat_id": CHAT_ID,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "HTML"
    }
    requests.post(url, data=data)


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url,
                  data={
                      "chat_id": CHAT_ID,
                      "text": message,
                      "parse_mode": "HTML"
                  })


def check_ads():
    sent_links = load_sent_links()

    for keyword, min_price, max_price in SEARCH_TARGETS:
        url = f"https://www.olx.kz/elektronika/telefony-i-aksesuary/mobilnye-telefony-smartfony/astana/?search[dist]=30&search[order]=created_at:desc&q={keyword.replace(' ', '%20')}"

        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")
        ads = soup.find_all("div", class_="css-13l3l78")

        for ad in ads:
            title_tag = ad.find("h6")
            price_tag = ad.find("h3", class_="css-fqcbii")
            link_tag = ad.find("a", href=True)
            img_tag = ad.find("img")

            if not (title_tag and price_tag and link_tag):
                continue

            title = title_tag.text.strip().lower()
            price_text = price_tag.text.strip().replace(" ", "").replace(
                "₸", "").replace("\xa0", "")
            link = "https://www.olx.kz" + link_tag["href"]
            img_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else None

            try:
                price = int(price_text)
            except ValueError:
                continue

            if link in sent_links:
                continue

            if any(bad in title for bad in BLACKLIST_KEYWORDS):
                continue

            if keyword in title and min_price <= price <= max_price:
                caption = (f"📱 <b>{title_tag.text.strip()}</b>\n"
                           f"💰 <b>{price} ₸</b>\n"
                           f"🔍 Поиск: <i>{keyword}</i>\n"
                           f"🔗 <a href='{link}'>Смотреть объявление</a>")

                if img_url:
                    send_photo(img_url, caption)
                    print(f"📷 Отправлено с фото: {title_tag.text.strip()}")
                else:
                    send_telegram(caption)
                    print(f"✅ Отправлено без фото: {title_tag.text.strip()}")

                save_sent_link(link)


# ✅ Flask-сервер для вызова через cron-job
app = Flask(__name__)


@app.route("/")
def home():
    return "✅ OLX бот работает!"

@app.route("/run")
def run_bot():
    print("🔁 Бот запущен, проверка начата")
    send_telegram("🤖 Бот начал проверку объявлений!")
    check_ads()
    return "🔁 Проверка объявлений выполнена!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
