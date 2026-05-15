import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def send_game_notification(game):
    store = game["store"]

    text = f'\u2501\u2501\u2501 {store} \u2501\u2501\u2501\n'
    text += f'{game["name"]}\n'

    if game.get("end_date"):
        text += f'По: {game["end_date"]}\n'

    text += f'\n{game["url"]}'

    try:
        resp = requests.post(
            f"{API_URL}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
            },
            timeout=15,
        )

        if not resp.ok:
            print(f"  Telegram error for '{game['name']}': {resp.text}")
        else:
            print(f"  Sent: {game['store']} - {game['name']}")
    except Exception as e:
        print(f"  Failed to send '{game['name']}': {e}")
