import json
from datetime import datetime, timezone
from pathlib import Path

from steam_tracker import get_steam_freebies
from epic_tracker import get_epic_freebies
from telegram_sender import send_game_notification

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

    sent_ids = load_sent()
    new_sent = set()
    new_games = []

    print("\n--- Steam ---")
    try:
        games = get_steam_freebies()
        for g in games:
            gid = f"steam_{g['id']}"
            new_sent.add(gid)
            if gid not in sent_ids:
                new_games.append(g)
        print(f"  Total: {len(games)}")
    except Exception as e:
        print(f"  Error: {e}")
        new_sent |= {s for s in sent_ids if s.startswith("steam_")}

    print("\n--- Epic Games ---")
    try:
        games = get_epic_freebies()
        for g in games:
            gid = f"epic_{g['id']}"
            new_sent.add(gid)
            if gid not in sent_ids:
                new_games.append(g)
        print(f"  Total: {len(games)}")
    except Exception as e:
        print(f"  Error: {e}")
        new_sent |= {s for s in sent_ids if s.startswith("epic_")}

    if new_games:
        print(f"\nSending {len(new_games)} new game(s) to Telegram...")
        for game in new_games:
            send_game_notification(game)

    save_sent(new_sent)
    print(f"\nDone! Saved {len(new_sent)} active IDs")


if __name__ == "__main__":
    main()
