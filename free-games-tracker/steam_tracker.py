import json
import requests
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

API_CATEGORIES = "https://store.steampowered.com/api/featuredcategories"
API_SEARCH = "https://store.steampowered.com/search/results/"
API_DETAILS = "https://store.steampowered.com/api/appdetails"
STORE_URL = "https://store.steampowered.com/app/{}"

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
MSK = timezone(timedelta(hours=3))

KNOWN_FREE_IDS = ["3587490", "3343840"]
SCAN_CHUNK = 1000
SCAN_INITIAL_OFFSET = 5000
SCAN_FILE = Path(__file__).parent / "steam_scan_progress.json"

RUS_MONTHS = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
    "мая": 5, "июня": 6, "июля": 7, "августа": 8,
    "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
}


def format_date(ts):
    if ts and ts > 0:
        return (
            datetime.fromtimestamp(ts, tz=timezone.utc)
            .astimezone(MSK)
            .strftime("%d.%m.%Y")
        )
    return None


def parse_steam_page_date(html):
    m = re.search(r'бесплатно до (\d{1,2})\s+([а-яё]+)\s+в\s+(\d{1,2}:\d{2})', html, re.IGNORECASE)
    if m:
        day = int(m.group(1))
        month_name = m.group(2).lower()
        month = RUS_MONTHS.get(month_name)
        if month:
            now = datetime.now(MSK)
            year = now.year
            if month < now.month:
                year += 1
            return f"{day:02d}.{month:02d}.{year}"
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
        price = app.get("price_overview")
        if not price:
            return None

        is_free_promo = price.get("discount_percent") == 100
        if not is_free_promo and app.get("is_free") and price.get("initial", 0) > 0:
            is_free_promo = True

        if not is_free_promo:
            return None

        initial = price.get("initial", 0)
        if not initial or initial <= 0:
            return None

        if not end_date:
            try:
                page = session.get(
                    STORE_URL.format(appid),
                    headers={**HEADERS, "Accept-Language": "ru-RU,ru;q=0.9"},
                    timeout=10,
                )
                end_date = parse_steam_page_date(page.text)
            except Exception:
                pass

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


LOGO_ID_PATTERN = re.compile(r"steam/apps/(\d+)")


def extract_app_id(item):
    raw = item.get("id")
    if raw:
        return str(raw)
    logo = item.get("logo") or ""
    m = LOGO_ID_PATTERN.search(logo)
    if m:
        return m.group(1)
    return None


def search_free_games():
    candidates = {}
    try:
        resp = requests.get(
            API_SEARCH,
            params={
                "maxprice": 0,
                "category1": 998,
                "hide_server_choice": 1,
                "json": 1,
                "count": 200,
                "cc": "us",
                "l": "english",
            },
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("items", []):
            appid = extract_app_id(item)
            if appid:
                candidates[appid] = None
    except Exception as e:
        print(f"  free search error: {e}")
    return candidates


def search_specials():
    candidates = {}
    try:
        resp = requests.get(
            API_SEARCH,
            params={
                "specials": 1,
                "hide_server_choice": 1,
                "json": 1,
                "count": 200,
                "cc": "us",
                "l": "english",
            },
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("items", []):
            appid = extract_app_id(item)
            if appid:
                candidates[appid] = None
    except Exception as e:
        print(f"  specials search error: {e}")
    return candidates


def search_free_specials():
    candidates = {}
    try:
        resp = requests.get(
            API_SEARCH,
            params={
                "maxprice": "free",
                "specials": 1,
                "hide_server_choice": 1,
                "json": 1,
                "count": 200,
                "cc": "us",
                "l": "english",
            },
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("items", []):
            appid = extract_app_id(item)
            if appid:
                candidates[appid] = None
    except Exception as e:
        print(f"  free+specials search error: {e}")
    return candidates


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
                    appid = extract_app_id(item)
                    if appid:
                        end_ts = item.get("discount_expiration")
                        if appid not in candidates:
                            candidates[appid] = format_date(end_ts)
    except Exception as e:
        print(f"  featuredcategories error: {e}")

    for appid in search_specials():
        if appid not in candidates:
            candidates[appid] = None

    for appid in search_free_games():
        if appid not in candidates:
            candidates[appid] = None

    for appid in search_free_specials():
        if appid not in candidates:
            candidates[appid] = None

    return candidates


def load_scan_progress():
    try:
        if SCAN_FILE.exists():
            return json.loads(SCAN_FILE.read_text()).get("last_scanned_appid", 0)
    except Exception:
        pass
    return 0


def save_scan_progress(appid):
    SCAN_FILE.write_text(json.dumps({"last_scanned_appid": appid}, indent=2))


def find_max_appid(session):
    low, high = 1, 8000000
    max_valid = 0
    while low <= high:
        mid = (low + high) // 2
        try:
            r = session.get(
                API_DETAILS,
                params={"appids": mid, "cc": "us", "l": "english"},
                headers=HEADERS,
                timeout=10,
            )
            if r.json().get(str(mid), {}).get("success"):
                max_valid = mid
                low = mid + 1
            else:
                high = mid - 1
        except Exception:
            high = mid - 1
    return max_valid


def scan_new_apps(session):
    games = []
    last_scanned = load_scan_progress()
    try:
        current_max = find_max_appid(session)
    except Exception as e:
        print(f"  scan find_max error: {e}")
        return games

    if last_scanned == 0:
        last_scanned = max(0, current_max - SCAN_INITIAL_OFFSET)
        save_scan_progress(last_scanned)
        print(f"  Initial scan offset: {last_scanned}")

    if last_scanned >= current_max:
        return games

    end = min(last_scanned + SCAN_CHUNK, current_max)
    found = 0

    for appid in range(last_scanned + 1, end + 1):
        try:
            r = session.get(
                API_DETAILS,
                params={"appids": appid, "cc": "us", "l": "english"},
                headers=HEADERS,
                timeout=8,
            )
            info = r.json().get(str(appid), {})
            if not info.get("success"):
                continue
            app = info.get("data", {})
            price = app.get("price_overview")
            if not price:
                continue

            is_free_promo = price.get("discount_percent") == 100
            if not is_free_promo and app.get("is_free") and price.get("initial", 0) > 0:
                is_free_promo = True

            if not is_free_promo:
                continue

            initial = price.get("initial", 0)
            if not initial or initial <= 0:
                continue

            end_date = None
            try:
                page = session.get(
                    STORE_URL.format(appid),
                    headers={**HEADERS, "Accept-Language": "ru-RU,ru;q=0.9"},
                    timeout=10,
                )
                end_date = parse_steam_page_date(page.text)
            except Exception:
                pass

            games.append({
                "store": "Steam",
                "id": str(appid),
                "name": app.get("name", "Unknown"),
                "url": STORE_URL.format(appid),
                "image": app.get("header_image", ""),
                "end_date": end_date,
                "original_price": initial,
            })
            found += 1
            print(f"  Scanned & found: {app.get('name', 'Unknown')} ({appid})")
        except Exception:
            continue

    save_scan_progress(end)
    print(f"  Scanned app IDs {last_scanned + 1}-{end}, found {found} free game(s)")
    return games


def get_steam_freebies():
    games = []
    session = requests.Session()
    session.headers.update(HEADERS)

    candidates = collect_candidates()

    for appid, end_date in sorted(candidates.items()):
        game = check_app(session, appid, end_date)
        if game:
            games.append(game)

    scanned = scan_new_apps(session)
    games.extend(scanned)

    session.close()
    return games
