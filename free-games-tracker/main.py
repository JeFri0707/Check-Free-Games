import json
from datetime import datetime, timezone
from pathlib import Path

from steam_tracker import get_steam_freebies
from epic_tracker import get_epic_freebies
from telegram_sender import send_text, send_game_notification

DATA_FILE = Path(__file__).parent / "sent_games.json"


def load_sent():
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            return set(json.load(f).get("sent_ids", []))
    return set()


def save_sent(ids):
    with open(DATA_FILE, "w") as f:
        json.dump(
            {
                "sent_ids": sorted(ids),
                "last_updated": datetime.now(timezone.utc).isoformat(),
            },
            f,
            indent=2,
        )


def main():
    print("=" * 40)
    print("  Free Games Tracker")
    print("=" * 40)

    send_text("🔍 <b>Проверка бесплатных игр...</b>\nИщу акции в Steam и Epic Games")

    sent_ids = load_sent()
    new_games = []

    print("\n--- Steam ---")
    try:
        games = get_steam_freebies()
        before = len(new_games)
        for g in games:
            gid = f"steam_{g['id']}"
            if gid not in sent_ids:
                sent_ids.add(gid)
                new_games.append(g)
        print(f"  Total: {len(games)}, New: {len(new_games) - before}")
    except Exception as e:
        print(f"  Error: {e}")

    print("\n--- Epic Games ---")
    try:
        games = get_epic_freebies()
        before = len(new_games)
        for g in games:
            gid = f"epic_{g['id']}"
            if gid not in sent_ids:
                sent_ids.add(gid)
                new_games.append(g)
        print(f"  Total: {len(games)}, New: {len(new_games) - before}")
    except Exception as e:
        print(f"  Error: {e}")

    if not new_games:
        print("\nNo new free games found.")
        send_text("✅ <b>Проверка завершена</b>\nНовых бесплатных игр не найдено")
        return

    print(f"\nSending {len(new_games)} new game(s) to Telegram...")
    for game in new_games:
        send_game_notification(game)

    save_sent(sent_ids)
    send_text(f"✅ <b>Проверка завершена</b>\nНайдено новых игр: {len(new_games)}")
    print("\nDone!")


if __name__ == "__main__":
    main()
