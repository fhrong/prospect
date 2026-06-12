from workers.proxy_service import (
    load_proxies_from_file,
    retest_proxies,
    stop_event,
)
#python -m workers.proxy_worker


if __name__ == "__main__":

    load_proxies_from_file()

    try:
        retest_proxies()

    except KeyboardInterrupt:
        print("Stopping proxy worker...")
        stop_event.set()