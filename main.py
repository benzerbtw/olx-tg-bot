import os
import requests
from bs4 import BeautifulSoup
from flask import Flask

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
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
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, data=data)

def check_ads():
    sent_links = load_sent_links()
    url = "https://www.olx.kz/elektronika/telefony-i-aksesuary/mobilnye-telefony-smartfony/astana/?search[order]=created_at:desc"
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    ads = soup.find_all("div", class_="css-u2ayx9")  # Актуальный класс блока
    for ad in ads:
        title_tag = ad.find("h4", class_="css-1g61gc2")
        price_tag = ad.find("p", class_="css-uj7mm0")
        link_tag = ad.find("a", href=True)
        img_tag = ad.find("img")

        if not (title_tag and price_tag and link_tag):
            continue

        title = title_tag.text.strip()
        price_text = price_tag.text.strip().replace(" ", "").replace("₸", "")
        link = "https://www.olx.kz" + link_tag["href"]
        img_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else None

        try:
            price = int(price_text)
        except:
            continue

        if link in sent_links:
            continue

        caption = (
            f"📱 <b>{title}</b>\n"
            f"💰 <b>{price} ₸</b>\n"
            f"🔗 <a href='{link}'>Смотреть объявление</a>"
        )

        if img_url:
            send_photo(img_url, caption)
        else:
            send_telegram(caption)

        save_sent_link(link)
        print("📤 Объявление отправлено:", title)

# Flask
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
