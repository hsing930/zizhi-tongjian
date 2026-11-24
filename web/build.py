"""
產生網站用的資料（只讀取 ../data，寫入 web/data/）。

用法（在專案根目錄或 web/ 目錄皆可）：
    python web/build.py

產出：
    web/data/juanNNN.json   每卷完整結構（壓縮格式，內容與 data/ 相同）
    web/data/meta.json      卷目錄、朝代分組、時間線索引
    web/data/entities/      若 data/entities/ 存在則一併複製（供日後人物/地名連結使用）
"""
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "data"
OUT = HERE / "data"

DYNASTY_RE = re.compile(r"(後(?:梁|唐|晉|晋|漢|周)|周|秦|漢|魏|晉|晋|宋|齊|梁|陳|隋|唐)紀")
# 年號標題括號內的西元年，例如「（己卯，西元前四〇二年）」「（壬辰，前二〇九年）」「（甲子，公元784年）」
YEAR_RE = re.compile(r"[，,]\s*(?:西元|公元)?(前|後)?([0-9〇一二三四五六七八九十百千零]+)年")

DIGITS = {"〇": 0, "零": 0, "一": 1, "二": 2, "三": 3, "四": 4,
          "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
UNITS = {"十": 10, "百": 100, "千": 1000}


def cn_to_int(s):
    """把「四〇二」「二十五」「一百二十」「784」轉成整數。"""
    if s.isdigit():
        return int(s)
    if any(c in UNITS for c in s):
        total, num = 0, 0
        for c in s:
            if c in DIGITS:
                num = DIGITS[c]
            elif c in UNITS:
                total += (num or 1) * UNITS[c]
                num = 0
        return total + num
    return int("".join(str(DIGITS[c]) for c in s if c in DIGITS))


def parse_year(heading):
    """回傳西元年（前年為負數，例如前 403 年 = -403）；無法解析時回傳 None。"""
    if not heading:
        return None
    matches = list(YEAR_RE.finditer(heading))
    if not matches:
        return None
    m = matches[-1]
    try:
        n = cn_to_int(m.group(2))
    except (KeyError, ValueError):
        return None
    return -n if m.group(1) == "前" else n


def clean_title(title, juan):
    """清理卷名：去掉【】、◎ 之後的註記文字，空白則用「第N卷」。"""
    t = (title or "").replace("【】", "").strip()
    t = re.sub(r"◎.*$", "", t).strip()
    t = re.sub(r"\s+", " ", t)
    return t or f"第{juan}卷"


def main():
    if not SRC.is_dir():
        sys.exit(f"找不到資料目錄：{SRC}")
    OUT.mkdir(parents=True, exist_ok=True)

    index = json.loads((SRC / "_index.json").read_text(encoding="utf-8"))
    index_by_juan = {e["juan"]: e for e in index}

    juans = []
    timeline = []
    unparsed = 0
    current_dynasty = None
    dynasties = []

    for e in sorted(index, key=lambda x: x["juan"]):
        n = e["juan"]
        src_file = SRC / f"juan{n:03d}.json"
        data = json.loads(src_file.read_text(encoding="utf-8"))

        # 朝代：依卷名推斷，沒有則沿用前一卷
        m = DYNASTY_RE.search(data.get("title") or e.get("title") or "")
        if m:
            name = m.group(1).replace("晋", "晉") + "紀"
            current_dynasty = name
        dynasty = current_dynasty or "其他"
        if dynasty not in dynasties:
            dynasties.append(dynasty)

        sections_meta = []
        for si, sec in enumerate(data["sections"]):
            y = parse_year(sec.get("year_heading"))
            if sec.get("year_heading"):
                if y is None:
                    unparsed += 1
                else:
                    timeline.append({"y": y, "juan": n, "sec": si,
                                     "heading": sec.get("heading") or "",
                                     "label": sec["year_heading"]})
            sections_meta.append({"heading": sec.get("heading") or "",
                                  "year_heading": sec.get("year_heading"),
                                  "events": len(sec.get("events", [])),
                                  "comments": len(sec.get("comments", []))})

        juans.append({
            "n": n,
            "title": clean_title(e.get("title") or data.get("title"), n),
            "dynasty": dynasty,
            "period": data.get("period") or "",
            "events": e.get("events", 0),
            "comments": e.get("comments", 0),
            "notes": e.get("notes", 0),
            "sections": sections_meta,
        })

        (OUT / f"juan{n:03d}.json").write_text(
            json.dumps(data, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8")

    timeline.sort(key=lambda t: (t["y"], t["juan"], t["sec"]))
    meta = {
        "juan_count": len(juans),
        "event_total": sum(j["events"] for j in juans),
        "comment_total": sum(j["comments"] for j in juans),
        "dynasties": dynasties,
        "juans": juans,
        "timeline": timeline,
        "timeline_unparsed": unparsed,
    }
    (OUT / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    ent_src = SRC / "entities"
    if ent_src.is_dir():
        shutil.copytree(ent_src, OUT / "entities", dirs_exist_ok=True)
        print(f"已複製 entities/（{ent_src}）")

    print(f"卷數 {len(juans)}，事件 {meta['event_total']}，論斷 {meta['comment_total']}")
    print(f"朝代分組 {len(dynasties)} 段：{' '.join(dynasties)}")
    print(f"時間線條目 {len(timeline)}，無法解析西元年的年號 {unparsed}")


if __name__ == "__main__":
    main()
