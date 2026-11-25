#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""產生 maps/links.json：地名 ↔ 歷史地圖來源的「連結層」。

原則（見 maps/README.md）：
- 只產生連結（URL 與授權狀態），不下載、不儲存任何受限 GIS 或地圖檔案。
- 授權不明確者一律標示 status = "待確認"。
- 地名清單來源（依優先順序，取第一個存在者）：
    1. 命令列 --places 指定的檔案
    2. data/entities/places.json
    3. data/entities/places_verified.json（另一子工作階段產生；狀態為 rejected_* 者排除）
    4. 上列 2–3 於主倉庫（git common dir 所在的主工作目錄）下的同名檔案
       （data/entities/ 為未追蹤檔，worktree 內可能不存在）
  若皆不存在，則以 data/juan*.json 事件文字掃描一組種子地名作為暫定清單，並在輸出中註明。

用法（在 maps 工作目錄執行）：
    python scripts/build_map_links.py
    python scripts/build_map_links.py --places path/to/places_verified.json

只讀取 data/（與 --places 指定檔），只寫入 maps/links.json。可重複執行，結果具決定性。
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT, "data")
OUT_PATH = os.path.join(ROOT, "maps", "links.json")
REJECTED_PREFIX = "rejected"

# ---- 來源目錄（URL 與授權摘要於 2026-11-25 重新驗證；詳見 maps/sources.md）----
SOURCES = {
    "chgis_v6": {
        "name": "CHGIS V6（哈佛 Fairbank Center / 復旦歷史地理研究中心）",
        "url": "https://chgis.fas.harvard.edu/data/chgis/v6/",
        "period": "頁面未載明年代範圍（待確認）；版本含 Time Series 與 1820/1911/1990 切片",
        "license": "License: free for academic research, no commercial use, resale, or redistribution permitted.",
        "can_link": True,
        "can_save_derived": False,
        "status": "連結可用；範圍與 Dataverse 逐資料集條款待確認",
    },
    "pitt_song_gazetteer": {
        "name": "The Digital Gazetteer of the Song Dynasty（匹茲堡大學）",
        "url": "https://d-scholarship.pitt.edu/44108/",
        "period": "宋（頁面標示 0960–1276；摘要寫 906–1276，以頁面為準）",
        "license": "Creative Commons BY-ND Attribution-NoDerivatives 4.0 International",
        "can_link": True,
        "can_save_derived": False,
        "status": "連結可用；ND 禁止改作後再散布",
    },
    "commons_svg_china_history": {
        "name": "Wikimedia Commons：Category:SVG maps of the history of China（119 檔）",
        "url": "https://commons.wikimedia.org/wiki/Category:SVG_maps_of_the_history_of_China",
        "period": "戰國至唐等（逐檔不同）",
        "license": "逐檔不同：已抽查 CC0 1.0（742nian_Tang.svg）、CC BY-SA 4.0（China_-_Song_Dynasty-mk.svg）",
        "can_link": True,
        "can_save_derived": "待確認",
        "status": "連結可用；保存派生資料須逐檔確認授權",
    },
    "prc_atlas_commons": {
        "name": "Wikimedia Commons：Category:Atlas of the People's Republic of China",
        "url": "https://commons.wikimedia.org/wiki/Category:Atlas_of_the_People%27s_Republic_of_China",
        "period": "未確認",
        "license": "未確認（2026-11-25 驗證仍回 HTTP 404）",
        "can_link": "待確認",
        "can_save_derived": "待確認",
        "status": "待確認：分類頁回 404，不列為可用連結",
    },
}

# 朝代 → 可連結來源（依來源頁面明確涵蓋的範圍；未涵蓋者不硬連）
DYNASTY_SOURCES = {
    "宋": ["pitt_song_gazetteer", "chgis_v6", "commons_svg_china_history"],
    "唐": ["chgis_v6", "commons_svg_china_history"],
    "漢": ["commons_svg_china_history"],
    "秦": ["commons_svg_china_history"],
    "周": ["commons_svg_china_history"],
}
NO_SOURCE_NOTE = "目前無已驗證的開放來源，待確認（見 maps/README.md 待決定事項）"

# 種子地名（暫定，僅在無任何地名清單檔時使用）。
SEED_PLACES = [
    "長安", "洛陽", "建康", "金陵", "開封", "汴州", "臨淄", "咸陽", "成都",
    "江陵", "襄陽", "鄴", "邯鄲", "大梁", "壽春", "荊州", "益州", "涼州",
    "幽州", "并州", "雍州", "揚州", "徐州", "兗州", "冀州", "青州", "豫州",
    "廣州", "潼關", "函谷關", "雁門", "玉門", "大散關", "河東", "河北",
    "河南", "關中", "江東", "淮南", "隴右", "河西", "漢中", "太原", "晉陽",
    "薊", "平城", "廣陵", "會稽", "彭城", "睢陽", "潁川", "南陽",
]

# 卷標題中的「X紀」→ 朝代（例：「第一卷　周紀一」→ 周）
RE_DYNASTY = re.compile(r"([一-鿿])紀")


def main_worktree_root():
    """回傳主倉庫工作目錄（worktree 之外）；失敗時回傳 None。"""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        return os.path.dirname(os.path.normpath(out))
    except Exception:
        return None


def candidate_place_files(cli_path):
    if cli_path:
        yield os.path.abspath(cli_path)
        return
    names = ["places.json", "places_verified.json"]
    for n in names:
        yield os.path.join(ROOT, "data", "entities", n)
    main = main_worktree_root()
    if main and os.path.normpath(main) != os.path.normpath(ROOT):
        for n in names:
            yield os.path.join(main, "data", "entities", n)


def load_place_names(cli_path):
    """回傳 (名稱清單, 輸入說明) 或 (None, None)。"""
    for path in candidate_place_files(cli_path):
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        items = raw if isinstance(raw, list) else raw.get("places", [])
        names = []
        statuses = {}
        excluded = 0
        for it in items:
            if isinstance(it, str):
                names.append(it)
            elif isinstance(it, dict) and it.get("name"):
                status = str(it.get("status") or "")
                if status.startswith(REJECTED_PREFIX):
                    excluded += 1
                    continue
                names.append(it["name"])
                if status:
                    statuses[it["name"]] = status
        note = f"{path}（排除 rejected_* {excluded} 筆）" if excluded else path
        return sorted(set(names)), statuses, note
    return None, {}, None


def scan_juans():
    """逐卷讀取事件文字，回傳 (卷號→朝代, 卷號→全文)。"""
    juan_dynasty = {}
    juan_text = {}
    for path in sorted(glob.glob(os.path.join(DATA_DIR, "juan*.json"))):
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        n = d["juan"]
        m = RE_DYNASTY.search(d.get("title") or "")
        juan_dynasty[n] = m.group(1) if m else None
        parts = []
        for sec in d.get("sections", []):
            if sec.get("year_heading"):
                parts.append(sec["year_heading"])
            for ev in sec.get("events", []):
                parts.append(ev.get("text") or "")
        juan_text[n] = "".join(parts)
    return juan_dynasty, juan_text


def build(cli_path):
    juan_dynasty, juan_text = scan_juans()
    place_names, verif_status, source_note = load_place_names(cli_path)
    if place_names is not None:
        input_note = source_note
        is_provisional = False
    else:
        place_names = SEED_PLACES
        input_note = ("暫定：無 data/entities/places*.json，"
                      "以 data/juan*.json 事件文字掃描種子地名（待更新）")
        is_provisional = True

    places = []
    unmatched = 0
    for name in place_names:
        hits = [n for n in sorted(juan_text) if name in juan_text[n]]
        if not hits:
            unmatched += 1
            continue
        dynasties = sorted({juan_dynasty[n] for n in hits if juan_dynasty[n]})
        source_keys = []
        for dyn in dynasties:
            for key in DYNASTY_SOURCES.get(dyn, []):
                if key not in source_keys:
                    source_keys.append(key)
        if source_keys:
            links = [{"source": k, "url": SOURCES[k]["url"], "status": SOURCES[k]["status"]}
                     for k in source_keys]
        else:
            links = [{"source": None, "status": "待確認", "note": NO_SOURCE_NOTE}]
        places.append({
            "name": name,
            "verification": verif_status.get(name),
            "juan_hits": len(hits),
            "juans_first": hits[:5],
            "dynasties": dynasties,
            "links": links,
        })

    places.sort(key=lambda p: (-p["juan_hits"], p["name"]))

    out = {
        "generated_by": "scripts/build_map_links.py",
        "place_input": input_note,
        "provisional": is_provisional,
        "policy": "link_only：只連結，不下載、不保存受限 GIS/圖資派生資料",
        "place_count": len(places),
        "places_not_found_in_juans": unmatched,
        "sources": SOURCES,
        "places": places,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"wrote {os.path.relpath(OUT_PATH, ROOT)}: {len(places)} places "
          f"({unmatched} not found in juans), provisional={is_provisional}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--places", help="地名清單 JSON 路徑（list 或含 places 的 dict）")
    args = ap.parse_args()
    build(args.places)
