import os
import sys
import json
import time
import requests
import undetected_chromedriver as uc
from threading import Thread, Event
from app.services.lead_finder import criar_driver
from fastapi import APIRouter, FastAPI,  HTTPException
from pydantic import BaseModel
from datetime import datetime

#uvicorn workers.proxy_provider:app --reload --host 0.0.0.0 --port 8001
# --- Run it from prospect folder

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
DATA_FOLDER = os.path.join(PROJECT_ROOT, "workers", "data")
JSON_PATH = os.path.join(DATA_FOLDER, "proxies.json")
os.makedirs(DATA_FOLDER, exist_ok=True)

proxy_pool = {}  # proxy -> metadata dict

PROXY_SOURCE_URL = (
    "https://api.proxyscrape.com/v4/free-proxy-list/get"
    "?request=display_proxies"
    "&proxy_format=protocolipport"
    "&format=text"
)
PROXY_TEST_INTERVAL = 300  # 5 mins
TEST_URL = "https://api.ipify.org"

stop_event = Event()

def save_proxies_to_file():
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        # Filtra apenas proxies saudáveis para salvar
        serializable_pool = {
            proxy: {
                **meta,
                "last_test": meta["last_test"].isoformat() if meta["last_test"] else None,
                "last_fail_time": meta["last_fail_time"].isoformat() if meta["last_fail_time"] else None,
            }
            for proxy, meta in proxy_pool.items()
            if meta.get("healthy")
        }
        json.dump(serializable_pool, f, indent=2)


def load_proxies_from_file():
    global proxy_pool
    if not os.path.exists(JSON_PATH):
        print(f"Arquivo JSON não encontrado em {JSON_PATH}. Começando com lista vazia.")
        return

    if os.path.getsize(JSON_PATH) == 0:
        print(f"Arquivo JSON em {JSON_PATH} está vazio. Começando com lista vazia.")
        return

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        loaded = json.load(f)
        proxy_pool = {}
        for proxy, meta in loaded.items():
            proxy_pool[proxy] = {
                **meta,
                "last_test": datetime.fromisoformat(meta["last_test"]) if meta["last_test"] else None,
                "last_fail_time": datetime.fromisoformat(meta["last_fail_time"]) if meta["last_fail_time"] else None,
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
            print(f"✅ OK | {proxy} | IP: {ip} | latency: {latency:.2f}s")
            return True, latency
        else:
            print(f"❌ No response body | {proxy}")
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
        print("Fetching fresh proxy list...")
        resp = requests.get(PROXY_SOURCE_URL, timeout=10)
        resp.raise_for_status()
        proxy_lines = resp.text.splitlines()
        return [p.strip() for p in proxy_lines if p.strip()]
    except Exception as ex:
        print(f"Error fetching proxies: {ex}")
        return []


def update_proxy_pool():
    new_proxies = fetch_proxies()
    now = datetime.utcnow()
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
    latency_score = meta["latency"] if meta["latency"] is not None else 999
    return fail_penalty + latency_score


def retest_proxies():
    print("Starting proxy retest loop...")
    while not stop_event.is_set():
        update_proxy_pool()
        for proxy, meta in proxy_pool.items():
            if meta["last_test"] and (datetime.utcnow() - meta["last_test"]).total_seconds() < 60:
                if meta["healthy"]:
                    continue

            healthy, latency = test_proxy(proxy)
            meta["last_test"] = datetime.utcnow()
            if healthy:
                meta["success"] += 1
                meta["healthy"] = True
                meta["latency"] = latency
                meta["last_fail_time"] = None
            else:
                meta["fail"] += 1
                meta["healthy"] = False
                meta["last_fail_time"] = datetime.utcnow()

            save_proxies_to_file()  # save after each test for persistence

        print("Retest cycle complete. Sleeping until next cycle...")
        stop_event.wait(PROXY_TEST_INTERVAL)


def get_best_proxies(top_n=10):
    healthy_proxies = [p for p, m in proxy_pool.items() if m.get("healthy")]
    if not healthy_proxies:
        # Carrega diretamente do JSON os proxies saudáveis ordenados por last_test
        if os.path.exists(JSON_PATH) and os.path.getsize(JSON_PATH) > 0:
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                # Filtra saudáveis (healthy = True) e ordena por last_test decrescente
                candidates = {
                    p: m for p, m in loaded.items() if m.get("healthy") is True
                }
                sorted_candidates = sorted(
                    candidates.items(),
                    key=lambda item: datetime.fromisoformat(item[1]["last_test"]) if item[1]["last_test"] else datetime.min,
                    reverse=True,
                )
                return [p for p, _ in sorted_candidates[:top_n]]
        else:
            return []
    sorted_proxies = sorted(healthy_proxies, key=lambda p: score_proxy(proxy_pool[p]))
    return sorted_proxies[:top_n]


def start_proxy_worker():
    load_proxies_from_file()
    worker_thread = Thread(target=retest_proxies, daemon=True)
    worker_thread.start()
    return worker_thread



router = APIRouter()  # Correto: APIRouter em vez de FastAPI()
class ProxyReport(BaseModel):
    proxy: str
@router.get("/proxy/best")
def get_best_proxy():
    best = get_best_proxies(top_n=1)
    if not best:
        raise HTTPException(status_code=404, detail="No healthy proxy available")
    return {"proxy": best[0]}
@router.post("/proxy/report_bad")
def report_bad_proxy(report: ProxyReport):
    proxy = report.proxy
    meta = proxy_pool.get(proxy)
    if not meta:
        raise HTTPException(status_code=404, detail="Proxy not found")
    meta['healthy'] = False
    meta['fail'] += 1
    meta['last_fail_time'] = datetime.utcnow()
    save_proxies_to_file()
    return {"status": "reported", "proxy": proxy}


app = FastAPI()
app.include_router(router)

worker = None

@app.on_event("startup")
def startup_event():
    load_proxies_from_file()
    print(f"Proxies carregados: {len(proxy_pool)}")
    print(f"Proxies saudáveis no início: {len([p for p in proxy_pool.values() if p.get('healthy')])}")
    global worker, stop_event
    stop_event.clear()
    worker = Thread(target=retest_proxies, daemon=True)
    worker.start()
    print("Proxy worker iniciado.")

@app.on_event("shutdown")
def shutdown_event():
    global stop_event, worker
    stop_event.set()
    if worker:
        worker.join()
    print("Proxy worker finalizado.")
