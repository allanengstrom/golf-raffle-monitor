import requests
import json
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timezone

KEYWORDS = ["raffle", "giveaway", "sweepstakes", "enter to win", "win a", "contest"]

SMS_TO = "5713732274@vtext.com"
GMAIL_FROM = os.environ["GMAIL_ADDRESS"]
GMAIL_PASS = os.environ["GMAIL_APP_PASSWORD"]
SEEN_FILE = "seen_raffles.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}

# Each entry: (brand, url)
PAGES = [
    ("Titleist",    "https://www.titleist.com/promotions"),
    ("Titleist",    "https://www.titleist.com/news"),
    ("TaylorMade",  "https://www.taylormadegolf.com/promotions"),
    ("TaylorMade",  "https://www.taylormadegolf.com/blogs/news"),
    ("Callaway",    "https://www.callawaygolf.com/promotions"),
    ("Callaway",    "https://www.callawaygolf.com/blogs/news"),
    ("PING",        "https://ping.com/en-us/promotions"),
    ("PING",        "https://ping.com/en-us/news"),
    ("Cobra",       "https://www.cobragolf.com/pages/promotions"),
    ("Cobra",       "https://www.cobragolf.com/blogs/news"),
    ("Cleveland",   "https://www.clevelandgolf.com/pages/promotions"),
    ("Cleveland",   "https://www.clevelandgolf.com/blogs/news"),
    ("Srixon",      "https://www.srixon.com/pages/promotions"),
    ("Srixon",      "https://www.srixon.com/blogs/news"),
    ("Mizuno",      "https://www.mizunousa.com/pages/golf-promotions"),
    ("Mizuno",      "https://www.mizunousa.com/blogs/news"),
    ("Bridgestone", "https://www.bridgestonegolf.com/en-us/promotions"),
    ("Bridgestone", "https://www.bridgestonegolf.com/en-us/news"),
    ("PGA Tour Superstore", "https://www.pgatoursuperstore.com/promotions"),
    ("Golf Galaxy", "https://www.golfgalaxy.com/c/golf-deals-promotions"),
    ("Global Golf", "https://www.globalgolf.com/promotions"),
]


def load_seen():
    try:
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(seen), f)


def url_is_live(url):
    try:
        r = requests.head(url, headers=HEADERS, timeout=10, allow_redirects=True)
        return r.status_code < 400
    except Exception:
        return False


def send_sms_batch(items):
    lines = [f"{item['brand']}: {item['url']}" for item in items]
    body = "GOLF RAFFLES:\n" + "\n".join(lines)
    msg = MIMEText(body)
    msg["From"] = GMAIL_FROM
    msg["To"] = SMS_TO
    msg["Subject"] = ""
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_FROM, GMAIL_PASS)
        server.send_message(msg)
    print(f"[SMS] Sent batch of {len(items)}")


def scrape_pages():
    results = []
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    for brand, url in PAGES:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code < 400 and any(kw in r.text.lower() for kw in KEYWORDS):
                results.append({
                    "id": f"{brand}_{today}",
                    "brand": brand,
                    "url": url,
                })
                print(f"[FOUND] {brand}: {url}")
            else:
                print(f"[CLEAR] {brand}: {url} (status={r.status_code})")
        except Exception as e:
            print(f"[WARN] {brand} {url}: {e}")
    return results


def main():
    seen = load_seen()
    findings = scrape_pages()

    seen_this_run = set()
    new_items = []
    for item in findings:
        key = item["id"]
        if key in seen or key in seen_this_run:
            continue
        seen_this_run.add(key)
        seen.add(key)
        new_items.append(item)

    for i in range(0, len(new_items), 3):
        batch = new_items[i:i + 3]
        try:
            send_sms_batch(batch)
        except Exception as e:
            print(f"[ERROR] SMS failed: {e}")

    save_seen(seen)
    print(f"Done. {len(new_items)} new raffle(s) found at {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()
