import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Set, Callable

from steam_tracker import get_steam_freebies
from epic_tracker import get_epic_freebies
from telegram_sender import send_game_notification

# =========================================================
# CHANGE 1:
# Added logging
# =========================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# =========================================================
# CHANGE 2:
# Constant file path
# =========================================================
DATA_FILE = Path(__file__).parent / "sent_games.json"

# =========================================================
# CHANGE 3:
# Platform configuration
# =========================================================
PLATFORMS = [
    ("Steam", "steam", get_steam_freebies),
    ("Epic Games", "epic", get_epic_freebies),
]


# =========================================================
# CHANGE 4:
# Added safer JSON loading
# =========================================================
def load_sent() -> Set[str]:
    if not DATA_FILE.exists():
        return set()

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("sent_ids", []))

    except (json.JSONDecodeError, OSError) as e:
        logging.error(f"Failed to load sent games: {e}")
        return set()


# =========================================================
# CHANGE 5:
# Added type hints
# =========================================================
def save_sent(ids: Set[str]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "sent_ids": sorted(ids),
                "last_updated": datetime.now(timezone.utc).isoformat(),
            },
            f,
            indent=2,
        )


# =========================================================
# CHANGE 6:
# Reusable platform processor
# =========================================================
def process_platform(
    name: str,
    prefix: str,
    fetch_func: Callable,
    sent_ids: Set[str],
):
    logging.info(f"Fetching {name} freebies...")

    new_sent = set()
    new_games = []

    try:
        games = fetch_func()

        for game in games:

            # =============================================
            # CHANGE 7:
            # Safer ID handling
            # =============================================
            game_id = game.get("id")

            if not game_id:
                continue

            gid = f"{prefix}_{game_id}"

            new_sent.add(gid)

            if gid not in sent_ids:
                new_games.append(game)

        logging.info(f"{name}: {len(games)} games found")

    except Exception as e:
        logging.error(f"{name} error: {e}")

        # Preserve old IDs if API fails
        new_sent |= {
            s for s in sent_ids if s.startswith(prefix)
        }

    return new_sent, new_games


def main():
    logging.info("=" * 40)
    logging.info("Free Games Tracker Started")
    logging.info("=" * 40)

    sent_ids = load_sent()

    all_sent = set()
    all_new_games = []

    # =====================================================
    # CHANGE 8:
    # Dynamic platform loop
    # =====================================================
    for name, prefix, fetch_func in PLATFORMS:

        platform_sent, platform_games = process_platform(
            name,
            prefix,
            fetch_func,
            sent_ids,
        )

        all_sent.update(platform_sent)
        all_new_games.extend(platform_games)

    # =====================================================
    # CHANGE 9:
    # Added limited threading
    # =====================================================
    if all_new_games:

        logging.info(
            f"Sending {len(all_new_games)} new game(s)..."
        )

        with ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(
                send_game_notification,
                all_new_games,
            )

    else:
        logging.info("No new games found")

    save_sent(all_sent)

    logging.info(
        f"Done! Saved {len(all_sent)} active IDs"
    )


if __name__ == "__main__":
    main()
