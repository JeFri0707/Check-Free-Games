import requests
from datetime import datetime, timezone, timedelta

API_CATEGORIES = "https://store.steampowered.com/api/featuredcategories"
API_SEARCH = "https://store.steampowered.com/search/results/"
API_DETAILS = "https://store.steampowered.com/api/appdetails"

STORE_URL = "https://store.steampowered.com/app/{}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

MSK = timezone(timedelta(hours=3))


def format_end_date(end_ts):
    if end_ts and end_ts > 0:
        return (
            datetime.fromtimestamp(end_ts, tz=timezone.utc)
            .astimezone(MSK)
            .strftime("%d.%m.%Y %H:%M")
        )
    return None


def parse_app_details(appid, data):
    if not data.get("success"):
        return None
    app = data.get("data", {})
    if app.get("type") != "game":
        return None
    price = app.get("price_overview")
    if not price:
        return None
    if price.get("discount_percent") != 100:
        return None
    initial = price.get("initial", 0)
    if not initial or initial <= 0:
        return None
    return {
        "store": "Steam",
        "id": str(appid),
        "name": app.get("name", "Unknown"),
        "url": STORE_URL.format(appid),
        "image": app.get("header_image", ""),
        "end_date": None,
        "original_price": initial,
    }


KNOWN_FREE_IDS = [
    "3587490",
]


def collect_candidate_ids():
    ids = set()

    for known_id in KNOWN_FREE_IDS:
        ids.add(known_id)

    try:
        resp = requests.get(
            API_CATEGORIES,
            params={"cc": "us", "l": "english"},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        for cat_name, cat_data in data.items():
            if isinstance(cat_data, dict) and "items" in cat_data:
                for item in cat_data["items"]:
                    item_id = item.get("id")
                    if item_id:
                        ids.add(str(item_id))
    except Exception as e:
        print(f"  featuredcategories error: {e}")

    try:
        resp = requests.get(
            API_SEARCH,
            params={"specials": 1, "json": 1, "count": 200, "cc": "us", "l": "english"},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("items", []):
            item_id = item.get("id")
            if item_id:
                ids.add(str(item_id))
    except Exception as e:
        print(f"  search API error: {e}")

    return ids


def get_steam_freebies():
    games = []
    candidate_ids = collect_candidate_ids()

    if not candidate_ids:
        return games

    ids_list = sorted(candidate_ids)

    for i in range(0, len(ids_list), 20):
        batch = ids_list[i : i + 20]
        try:
            params = {"cc": "us", "l": "english"}
            params["appids"] = batch
            resp = requests.get(
                API_DETAILS,
                params=params,
                headers=HEADERS,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            for appid_str in batch:
                app_data = data.get(appid_str)
                if not app_data:
                    continue
                game = parse_app_details(appid_str, app_data)
                if game:
                    games.append(game)
        except Exception as e:
            print(f"  appdetails error (batch {i}): {e}")

    return games
