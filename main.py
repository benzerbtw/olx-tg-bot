import requests
from bs4 import BeautifulSoup
import os
from flask import Flask

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

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

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"})

def check_ads():
    sent_links = load_sent_links()
    keyword = "айфон 14"
    min_price = 0
    max_price = 150000

    url = f"https://www.olx.kz/d/elektronika/telefony/q-{keyword.replace(' ', '%20')}/?search[order]=created_at:desc&region=astana"
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    ads = soup.find_all("div", class_="css-13l3l78")  # обнови class_ если OLX его сменил

    for ad in ads:
        title_tag = ad.find("h6") or ad.find("h4")
        price_tag = ad.find("p", class_="css-uj7mm0") or ad.find("h3")
        link_tag = ad.find("a", href=True)
        img_tag = ad.find("img")

        if not (title_tag and price_tag and link_tag):
            continue

        title = title_tag.text.strip().lower()
        price_text = price_tag.text.strip().replace(" ", "").replace("₸", "").replace("\xa0", "")
        link = "https://www.olx.kz" + link_tag["href"]
        img_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else None

        try:
            price = int(price_text)
        except ValueError:
            continue

        if link in sent_links or "копия" in title or "реплика" in title:
            continue

        if "айфон 13" in title and min_price <= price <= max_price:
            caption = f"📱 <b>{title}</b>\n💰 <b>{price} ₸</b>\n🔗 <a href='{link}'>Смотреть объявление</a>"
            send_telegram(caption)
            print("✅ Отправлено:", title)
            save_sent_link(link)

# Flask-сервер
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Бот запущен!"

@app.route("/run")
def run_bot():
    send_telegram("🤖 Бот начал проверку объявлений (айфон 13 до 150к)!")
    check_ads()
    return "🔁 Проверка выполнена"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
