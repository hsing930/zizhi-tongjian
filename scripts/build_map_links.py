#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""產生 maps/links.json：地名 ↔ 歷史地圖來源的「連結層」。

原則（見 maps/README.md）：
- 只產生連結（URL 與授權狀態），不下載、不儲存任何受限 GIS 或地圖檔案。
- 授權不明確者一律標示 status = "待確認"。
- 地名清單優先讀取 data/entities/places.json（若存在）；否則以 data/juan*.json
  的事件文字掃描一組種子地名，作為暫定清單，並在輸出中註明。

用法（在專案根目錄執行）：
    python scripts/build_map_links.py

只讀取 data/，只寫入 maps/links.json。可重複執行，結果具決定性。
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT, "data")
ENTITY_PLACES = os.path.join(DATA_DIR, "entities", "places.json")
OUT_PATH = os.path.join(ROOT, "maps", "links.json")

# ---- 來源目錄（URL 與授權摘要於 2026-11-24 人工驗證；詳見 maps/sources.md）----
SOURCES = {
    "chgis_v6": {
        "name": "CHGIS V6（哈佛 Fairbank Center / 復旦歷史地理研究中心）",
        "url": "https://chgis.fas.harvard.edu/data/chgis/v6/",
        "period": "唐宋為主（頁面未載明年代範圍，待確認）",
        "license": "free for academic research, no commercial use, resale, or redistribution permitted",
        "can_link": True,
        "can_save_derived": False,
        "status": "連結可用；範圍待確認",
    },
    "pitt_song_gazetteer": {
        "name": "The Digital Gazetteer of the Song Dynasty（匹茲堡大學）",
        "url": "https://d-scholarship.pitt.edu/44108/",
        "period": "宋（頁面標示 0960–1276）",
        "license": "CC BY-ND 4.0",
        "can_link": True,
        "can_save_derived": False,
        "status": "連結可用；不得改作後再散布",
    },
    "commons_svg_china_history": {
        "name": "Wikimedia Commons：SVG maps of the history of China",
        "url": "https://commons.wikimedia.org/wiki/Category:SVG_maps_of_the_history_of_China",
        "period": "戰國至唐等（逐檔不同）",
        "license": "逐檔不同：例如 CC0 1.0、CC BY-SA 3.0/4.0（需逐檔確認）",
        "can_link": True,
        "can_save_derived": "待確認",
        "status": "連結可用；保存派生資料須逐檔確認授權",
    },
    "prc_atlas_commons": {
        "name": "Wikimedia Commons：Atlas of the People's Republic of China（分類）",
        "url": "https://commons.wikimedia.org/wiki/Category:Atlas_of_the_People%27s_Republic_of_China",
        "period": "未確認",
        "license": "未確認（驗證時回 HTTP 404）",
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

# 種子地名（暫定，僅在 data/entities/places.json 不存在時使用）。
# 只收錄明確屬地名（都城、州郡、關隘、大區）的詞，避開國名與人名。
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


def load_entity_places():
    """若有 data/entities/places.json，讀取其中的地名（支援字串清單或含 name 的物件清單）。"""
    if not os.path.exists(ENTITY_PLACES):
        return None
    with open(ENTITY_PLACES, encoding="utf-8") as f:
        raw = json.load(f)
    names = []
    items = raw if isinstance(raw, list) else raw.get("places", [])
    for it in items:
        if isinstance(it, str):
            names.append(it)
        elif isinstance(it, dict) and it.get("name"):
            names.append(it["name"])
    return sorted(set(names))


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


def build():
    juan_dynasty, juan_text = scan_juans()
    entity_names = load_entity_places()
    if entity_names is not None:
        place_names = entity_names
        input_note = "data/entities/places.json"
        is_provisional = False
    else:
        place_names = SEED_PLACES
        input_note = ("暫定：data/entities/places.json 尚不存在，"
                      "以 data/juan*.json 事件文字掃描種子地名（待更新）")
        is_provisional = True

    places = []
    for name in place_names:
        hits = [n for n in sorted(juan_text) if name in juan_text[n]]
        if not hits:
            continue
        dynasties = sorted({juan_dynasty[n] for n in hits if juan_dynasty[n]})
        links = []
        seen = set()
        for dyn in dynasties:
            for key in DYNASTY_SOURCES.get(dyn, []):
                if key in seen:
                    continue
                seen.add(key)
                src = SOURCES[key]
                links.append({
                    "source": key,
                    "name": src["name"],
                    "url": src["url"],
                    "basis": f"朝代「{dyn}」（卷標題）對應之來源；僅為來源層級連結，未驗證到個別地名",
                    "license": src["license"],
                    "status": src["status"],
                })
        if not links:
            links.append({"source": None, "status": "待確認", "note": NO_SOURCE_NOTE})
        places.append({
            "name": name,
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
        "sources": {k: {kk: vv for kk, vv in v.items()} for k, v in SOURCES.items()},
        "places": places,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"wrote {os.path.relpath(OUT_PATH, ROOT)}: {len(places)} places, provisional={is_provisional}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="ascii", errors="replace") if hasattr(sys.stdout, "reconfigure") else None
    build()
