# -*- coding: utf-8 -*-
"""
抓取維基文庫《資治通鑑》全书 294 卷的 wikitext（原始来源，保存為 UTF-8）。

- 来源：https://zh.wikisource.org  頁面 資治通鑑/卷001 … 卷294
- 只讀取公開頁面的 wikitext，不做登录、不绕過任何限制。
- 每次請求間隔 1 秒；已存在的文件会跳過（可断点續抓）。
- 輸出：raw/juan001.wiki … raw/juan294.wiki，以及 raw/_fetch_report.json
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import urllib.error

API = "https://zh.wikisource.org/w/api.php"
UA = "zizhi-tongjian-kb/0.1 (open-source knowledge base project; polite fetch, 1 req/s)"
BASE_TITLE = "資治通鑑/卷{n:03d}"
TOTAL = 294
SLEEP = 2.0
MAX_RETRY = 6

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(ROOT, "raw")


def fetch_wikitext(n: int) -> str:
    title = BASE_TITLE.format(n=n)
    params = {
        "action": "parse",
        "page": title,
        "prop": "wikitext",
        "format": "json",
        "formatversion": "2",
    }
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if "error" in data:
        raise RuntimeError(data["error"].get("info", "unknown API error"))
    return data["parse"]["wikitext"]


def main() -> int:
    os.makedirs(RAW, exist_ok=True)
    report = {"ok": [], "failed": [], "skipped": []}
    for n in range(1, TOTAL + 1):
        out = os.path.join(RAW, f"juan{n:03d}.wiki")
        if os.path.exists(out) and os.path.getsize(out) > 0:
            report["skipped"].append(n)
            continue
        text, last_err = None, ""
        for attempt in range(1, MAX_RETRY + 1):
            try:
                text = fetch_wikitext(n)
                break
            except urllib.error.HTTPError as e:
                last_err = f"HTTP {e.code}"
                if e.code == 429 or e.code >= 500:
                    wait = 30 * attempt  # 限流或服务端错误：退避後重試
                    print(f"[retry] juan{n:03d} {last_err}, wait {wait}s (attempt {attempt})")
                    time.sleep(wait)
                    continue
                break
            except (urllib.error.URLError, RuntimeError, KeyError, ValueError) as e:
                last_err = str(e)
                time.sleep(10)
        if text is not None:
            with open(out, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            report["ok"].append(n)
            print(f"[ok] juan{n:03d} {len(text)} chars")
        else:
            report["failed"].append({"juan": n, "error": last_err})
            print(f"[fail] juan{n:03d}: {last_err}")
        time.sleep(SLEEP)
    with open(os.path.join(RAW, "_fetch_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"done: ok={len(report['ok'])} skipped={len(report['skipped'])} failed={len(report['failed'])}")
    return 0 if not report["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
