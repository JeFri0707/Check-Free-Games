import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

STORE_ICONS = {"Steam": "🎮", "Epic Games": "🟣"}


def send_game_notification(game):
    icon = STORE_ICONS.get(game["store"], "🎯")

    text = (
        f"{icon} <b>{game['store']}: {game['name']}</b>\n\n"
        f"💰 <b>Бесплатно!</b> Была платной, теперь со скидкой 100%\n"
    )

    if game.get("end_date"):
        text += f"📅 Раздача до: {game['end_date']} МСК\n"

    text += f'🔗 <a href="{game["url"]}">Открыть в магазине</a>'

    image = game.get("image", "")

    try:
        if image:
            resp = requests.post(
                f"{API_URL}/sendPhoto",
                json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "photo": image,
                    "caption": text,
                    "parse_mode": "HTML",
                },
                timeout=15,
            )
        else:
            resp = requests.post(
                f"{API_URL}/sendMessage",
                json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": text,
                    "parse_mode": "HTML",
                },
                timeout=15,
            )

        if not resp.ok:
            print(f"  Telegram error for '{game['name']}': {resp.text}")
        else:
            print(f"  Sent: {game['store']} - {game['name']}")
    except Exception as e:
        print(f"  Failed to send '{game['name']}': {e}")
