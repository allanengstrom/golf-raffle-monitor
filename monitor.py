import requests
import json
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timezone
from urllib.parse import quote

BRANDS = [
    "Titleist", "TaylorMade", "Callaway", "PING",
    "Cobra", "Cleveland", "Srixon", "Mizuno", "Bridgestone"
]
KEYWORDS = ["raffle", "giveaway", "sweepstakes", "enter to win", "win a"]

SMS_TO = "5713732274@vtext.com"
GMAIL_FROM = os.environ["GMAIL_ADDRESS"]
GMAIL_PASS = os.environ["GMAIL_APP_PASSWORD"]
SEEN_FILE = "seen_raffles.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; GolfRaffleMonitor/1.0)"}


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


def is_relevant(text):
    text = text.lower()
    return any(kw in text for kw in KEYWORDS) and any(b.lower() in text for b in BRANDS)


def search_news_api():
    results = []
    api_key = os.environ["NEWS_API_KEY"]
    brands_query = " OR ".join(BRANDS)
    query = quote(f"({brands_query}) AND (raffle OR giveaway OR sweepstakes)")
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&pageSize=50&apiKey={api_key}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        for article in r.json().get("articles", []):
            title = article.get("title") or ""
            link = article.get("url") or ""
            if not link or not is_relevant(title):
                continue
            results.append({
                "id": f"news_{link}",
                "brand": next((b for b in BRANDS if b.lower() in title.lower()), "Golf"),
                "title": title,
                "url": link,
            })
    except Exception as e:
        print(f"[WARN] NewsAPI: {e}")
    return results


def scrape_brand_pages():
    pages = {
        "Titleist": "https://www.titleist.com/promotions",
        "TaylorMade": "https://www.taylormadegolf.com/promotions",
        "Callaway": "https://www.callawaygolf.com/promotions",
        "Cobra": "https://www.cobragolf.com/blogs/news",
        "PING": "https://ping.com/en-us/promotions",
        "Cleveland": "https://www.clevelandgolf.com/pages/promotions",
        "Srixon": "https://www.srixon.com/pages/promotions",
        "Bridgestone": "https://www.bridgestonegolf.com/en-us/promotions",
    }
    results = []
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    for brand, url in pages.items():
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code < 400 and any(kw in r.text.lower() for kw in KEYWORDS):
                results.append({
                    "id": f"brand_{brand}_{today}",
                    "brand": brand,
                    "title": f"Raffle/giveaway on {brand} promotions page",
                    "url": url,
                })
        except Exception as e:
            print(f"[WARN] Brand page {brand}: {e}")
    return results


def main():
    seen = load_seen()

    findings = []
    findings.extend(search_news_api())
    findings.extend(scrape_brand_pages())

    seen_this_run = set()
    new_items = []
    for item in findings:
        key = item["id"]
        if key in seen or key in seen_this_run:
            continue
        if not url_is_live(item["url"]):
            print(f"[SKIP] Dead link: {item['url']}")
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
