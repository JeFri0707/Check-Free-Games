import requests
from datetime import datetime, timezone, timedelta

API_URL = "https://store.steampowered.com/api/featuredcategories"
STORE_URL = "https://store.steampowered.com/app/{}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

MSK = timezone(timedelta(hours=3))


def get_steam_freebies():
    games = []
    resp = requests.get(
        API_URL,
        params={"cc": "ru", "l": "russian"},
        headers=HEADERS,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    for item in data.get("specials", {}).get("items", []):
        if item.get("discount_percent") != 100:
            continue

        orig = item.get("original_price", 0)
        if not orig or orig <= 0:
            continue

        end_ts = item.get("discount_expiration")
        if end_ts and end_ts > 0:
            end_date = (
                datetime.fromtimestamp(end_ts, tz=timezone.utc)
                .astimezone(MSK)
                .strftime("%d.%m.%Y %H:%M")
            )
        else:
            end_date = None

        games.append({
            "store": "Steam",
            "id": str(item["id"]),
            "name": item.get("name", "Unknown"),
            "url": STORE_URL.format(item["id"]),
            "image": item.get("header_image", ""),
            "end_date": end_date,
            "original_price": orig,
        })

    return games
