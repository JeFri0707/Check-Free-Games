import requests
from datetime import datetime, timezone, timedelta

API_CATEGORIES = "https://store.steampowered.com/api/featuredcategories"
API_SEARCH = "https://store.steampowered.com/search/results/"
API_DETAILS = "https://store.steampowered.com/api/appdetails"
STORE_URL = "https://store.steampowered.com/app/{}"

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
MSK = timezone(timedelta(hours=3))

KNOWN_FREE_IDS = ["3587490"]


def format_date(ts):
    if ts and ts > 0:
        return (
            datetime.fromtimestamp(ts, tz=timezone.utc)
            .astimezone(MSK)
            .strftime("%d.%m.%Y")
        )
    return None


def check_app(session, appid, end_date=None):
    try:
        r = session.get(
            API_DETAILS,
            params={"appids": appid, "cc": "us", "l": "english"},
            headers=HEADERS,
            timeout=10,
        )
        if r.status_code != 200:
            return None
        data = r.json().get(appid)
        if not data or not data.get("success"):
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
            "id": appid,
            "name": app.get("name", "Unknown"),
            "url": STORE_URL.format(appid),
            "image": app.get("header_image", ""),
            "end_date": end_date,
            "original_price": initial,
        }
    except Exception:
        return None


def collect_candidates():
    candidates = {}

    for known_id in KNOWN_FREE_IDS:
        candidates[known_id] = None

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
                        end_ts = item.get("discount_expiration")
                        sid = str(item_id)
                        if sid not in candidates:
                            candidates[sid] = format_date(end_ts)
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
                sid = str(item_id)
                if sid not in candidates:
                    candidates[sid] = None
    except Exception as e:
        print(f"  search API error: {e}")

    return candidates


def get_steam_freebies():
    games = []
    candidates = collect_candidates()

    if not candidates:
        return games

    session = requests.Session()
    session.headers.update(HEADERS)

    for appid, end_date in sorted(candidates.items()):
        game = check_app(session, appid, end_date)
        if game:
            games.append(game)

    session.close()
    return games
