import os
import sys
import json
import time
import requests
from threading import Event
from datetime import datetime
from app.services.lead_finder import criar_driver



PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

DATA_FOLDER = os.path.join(PROJECT_ROOT, "workers", "data")
JSON_PATH = os.path.join(DATA_FOLDER, "proxies.json")

os.makedirs(DATA_FOLDER, exist_ok=True)

proxy_pool = {}

PROXY_SOURCE_URL = (
    "https://api.proxyscrape.com/v4/free-proxy-list/get"
    "?request=display_proxies"
    "&proxy_format=protocolipport"
    "&format=text"
)

PROXY_TEST_INTERVAL = 300
TEST_URL = "https://api.ipify.org"

stop_event = Event()


def save_proxies_to_file():
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        serializable_pool = {
            proxy: {
                **meta,
                "last_test": meta["last_test"].isoformat()
                if meta["last_test"]
                else None,
                "last_fail_time": meta["last_fail_time"].isoformat()
                if meta["last_fail_time"]
                else None,
            }
            for proxy, meta in proxy_pool.items()
        }

        json.dump(serializable_pool, f, indent=2)


def load_proxies_from_file():
    global proxy_pool

    if not os.path.exists(JSON_PATH):
        return

    if os.path.getsize(JSON_PATH) == 0:
        return

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    proxy_pool.clear()

    for proxy, meta in loaded.items():
        proxy_pool[proxy] = {
            **meta,
            "last_test": datetime.fromisoformat(meta["last_test"])
            if meta.get("last_test")
            else None,
            "last_fail_time": datetime.fromisoformat(meta["last_fail_time"])
            if meta.get("last_fail_time")
            else None,
        }


def test_proxy(proxy, timeout=5):
    driver = None
    start = time.time()

    try:
        print(f"Testing {proxy}...")

        driver = criar_driver(proxy, True)

        driver.set_page_load_timeout(timeout)
        driver.get(TEST_URL)

        ip = driver.find_element("tag name", "body").text.strip()

        latency = time.time() - start

        if ip:
            print(f"✅ OK | {proxy} | {ip} | {latency:.2f}s")
            return True, latency

        return False, None

    except Exception as e:
        print(f"❌ Failed | {proxy} | {e}")
        return False, None

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def fetch_proxies():
    try:
        print("Fetching proxies...")

        resp = requests.get(PROXY_SOURCE_URL, timeout=10)
        resp.raise_for_status()

        return [
            p.strip()
            for p in resp.text.splitlines()
            if p.strip()
        ]

    except Exception as ex:
        print(ex)
        return []


def update_proxy_pool():
    new_proxies = fetch_proxies()

    for proxy in new_proxies:
        if proxy not in proxy_pool:
            proxy_pool[proxy] = {
                "success": 0,
                "fail": 0,
                "latency": None,
                "last_test": None,
                "healthy": None,
                "last_fail_time": None,
            }


def score_proxy(meta):
    fail_penalty = meta["fail"] * 10
    latency_score = meta["latency"] if meta["latency"] else 999

    return fail_penalty + latency_score


def get_best_proxies(top_n=10):
    load_proxies_from_file()

    healthy = [
        (proxy, meta)
        for proxy, meta in proxy_pool.items()
        if meta.get("healthy")
    ]

    healthy.sort(key=lambda item: score_proxy(item[1]))

    return [proxy for proxy, _ in healthy[:top_n]]


def mark_proxy_bad(proxy):
    load_proxies_from_file()

    if proxy not in proxy_pool:
        return False

    proxy_pool[proxy]["healthy"] = False
    proxy_pool[proxy]["fail"] += 1
    proxy_pool[proxy]["last_fail_time"] = datetime.utcnow()

    save_proxies_to_file()

    return True


def retest_proxies():
    print("Starting proxy retest loop...")

    while not stop_event.is_set():

        update_proxy_pool()

        for proxy, meta in list(proxy_pool.items()):

            if (
                meta["last_test"]
                and (
                    datetime.utcnow() - meta["last_test"]
                ).total_seconds() < 60
            ):
                if meta["healthy"]:
                    continue

            healthy, latency = test_proxy(proxy)

            meta["last_test"] = datetime.utcnow()

            if healthy:
                meta["healthy"] = True
                meta["success"] += 1
                meta["latency"] = latency
                meta["last_fail_time"] = None
            else:
                meta["healthy"] = False
                meta["fail"] += 1
                meta["last_fail_time"] = datetime.utcnow()

            save_proxies_to_file()

        print("Cycle complete")

        stop_event.wait(PROXY_TEST_INTERVAL)