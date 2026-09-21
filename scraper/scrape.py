import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://rdmotors.co.nz/our-vehicles/"
DATA_FILE = Path(__file__).parent.parent / "data" / "history.json"


def fetch_vehicles():
    response = requests.get(URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract all prices matching $X,XXX or $XX,XXX or $XXX,XXX patterns
    prices = []
    for tag in soup.find_all(string=re.compile(r"\$[\d,]+")):
        matches = re.findall(r"\$([\d,]+)", tag)
        for m in matches:
            value = int(m.replace(",", ""))
            # Sanity-check: vehicle prices between $1,000 and $500,000
            if 1_000 <= value <= 500_000:
                prices.append(value)

    return prices


def load_history():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    return []


def save_history(history):
    DATA_FILE.write_text(json.dumps(history, indent=2))


def main():
    try:
        prices = fetch_vehicles()
    except requests.exceptions.ConnectionError as e:
        print(f"WARNING: Could not reach {URL} — skipping this run.")
        print(f"  Detail: {e}")
        sys.exit(0)
    except requests.exceptions.HTTPError as e:
        print(f"WARNING: HTTP error fetching {URL} — skipping this run.")
        print(f"  Detail: {e}")
        sys.exit(0)
    except requests.exceptions.Timeout:
        print(f"WARNING: Request to {URL} timed out — skipping this run.")
        sys.exit(0)

    count = len(prices)
    total = sum(prices)

    if count == 0:
        print("WARNING: No vehicle prices found — page structure may have changed. Skipping.")
        sys.exit(0)

    print(f"Vehicles found: {count}")
    print(f"Total value:    ${total:,}")

    history = load_history()
    history.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "count": count,
        "total_value": total,
    })
    save_history(history)
    print("History updated.")


if __name__ == "__main__":
    main()
