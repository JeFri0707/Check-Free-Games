import requests, json

r = requests.get(
    "https://store.steampowered.com/search/results/",
    params={
        "maxprice": "free",
        "specials": 1,
        "hide_server_choice": 1,
        "json": 1,
        "count": 200,
        "cc": "us",
        "l": "english",
    },
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
    timeout=15,
)

data = r.json()
for item in data.get("items", [])[:10]:
    appid = item.get("id", "")
    logo = item.get("logo", "")
    exp = item.get("discount_expiration")
    print(f"appid={appid} logo_tail={logo[-20:]} exp={exp}")
