import requests
from bs4 import BeautifulSoup
import os
from flask import Flask

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Упрощённый фильтр — найдёт всё, что угодно
SEARCH_TARGETS = [
    ("", 0, 10000000),  # Пустой запрос — просто чтобы что-то найти
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
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    data = {"chat_id": CHAT_ID, "photo": photo_url, "caption": caption, "parse_mode": "HTML"}
    requests.post(url, data=data)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"})

def check_ads():
    sent_links = load_sent_links()

    for keyword, min_price, max_price in SEARCH_TARGETS:
        url = (
            f"https://www.olx.kz/elektronika/telefony-i-aksesuary/"
            f"mobilnye-telefony-smartfony/astana/?search[order]=created_at:desc"
        )
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")
        ads = soup.find_all("div", class_="css-13l3l78")  # Актуальный класс объявления

        for ad in ads:
            title_tag = ad.find("h6") or ad.find("h4")
            price_tag = ad.find("p", class_="css-uj7mm0") or ad.find("h3")
            link_tag = ad.find("a", href=True)
            img_tag = ad.find("img")

            if not (title_tag and price_tag and link_tag):
                continue

            title = title_tag.text.strip().lower()
            price_text = (
                price_tag.text.strip().replace(" ", "").replace("₸", "").replace("\xa0", "")
            )
            link = "https://www.olx.kz" + link_tag["href"]
            img_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else None

            try:
                price = int(price_text)
            except ValueError:
                continue

            if link in sent_links or any(bad in title for bad in BLACKLIST_KEYWORDS):
                continue

            if min_price <= price <= max_price:
                caption = (
                    f"📱 <b>{title_tag.text.strip()}</b>\n"
                    f"💰 <b>{price} ₸</b>\n"
                    f"🔗 <a href='{link}'>Смотреть объявление</a>"
                )

                if img_url:
                    send_photo(img_url, caption)
                else:
                    send_telegram(caption)

                print(f"✅ Отправлено: {title_tag.text.strip()}")
                save_sent_link(link)

# Flask
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
