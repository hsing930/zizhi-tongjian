# -*- coding: utf-8 -*-
"""
把 raw/juanNNN.wiki（維基文庫 wikitext）解析為結構化 JSON。

每卷輸出 data/juanNNN.json，結構：
{
  "juan": 1, "title": "第一卷　周紀一", "period": "起著雍攝提格…",
  "sections": [
    {"level": 2, "heading": "威烈王", "year_heading": null, "events": [...], "comments": [...]},
    ...
  ],
  "stats": {...}
}
events 項：{"no": 1, "text": "...", "notes": ["..."]}
comments 項（臣光曰）：{"text": "...", "notes": []}
"""
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(ROOT, "raw")
DATA = os.path.join(ROOT, "data")

RE_REF = re.compile(r"<ref[^>]*>(.*?)</ref>", re.S)
RE_REF_SELF = re.compile(r"<ref[^>]*/>")
RE_TEMPLATE = re.compile(r"\{\{[^{}]*\}\}")
RE_LINK_PIPE = re.compile(r"\[\[([^\]|]*)\|([^\]]*)\]\]")
RE_LINK = re.compile(r"\[\[([^\]]*)\]\]")
RE_BOLD = re.compile(r"'''")
RE_ITAL = re.compile(r"''")
RE_EVENT = re.compile(r"^'''(\d+)'''\s*(.*)$")
RE_HEADING = re.compile(r"^(={2,5})\s*(.+?)\s*\1\s*$")
RE_SECTION_TPL = re.compile(r"\|section=([^\n|}]+)")
RE_PERIOD = re.compile(r"^'''(起著.*?)'''\s*$", re.M)
# 无標記年号行：含"年（…公元/西元…）"
RE_PLAIN_YEAR = re.compile(r"年[（(][^）)]*(公元|西元)[^）)]*[）)]")


def clean_inline(s: str):
    """去掉 ref、模板、链接標記，返回 (纯文本, 注釋列表)。"""
    notes = [m.strip() for m in RE_REF.findall(s)]
    s = RE_REF.sub("", s)
    s = RE_REF_SELF.sub("", s)
    s = RE_TEMPLATE.sub("", s)
    s = RE_LINK_PIPE.sub(r"\2", s)
    s = RE_LINK.sub(r"\1", s)
    s = RE_BOLD.sub("", s)
    s = RE_ITAL.sub("", s)
    s = s.replace("<br>", "\n").replace("<br/>", "\n")
    s = re.sub(r"[ \t]+", " ", s).strip()
    return s, notes


def parse_juan(n: int, wikitext: str) -> dict:
    section_title = ""
    m = RE_SECTION_TPL.search(wikitext)
    if m:
        section_title = m.group(1).strip()

    period = ""
    pm = RE_PERIOD.search(wikitext)
    if pm:
        period, _ = clean_inline(pm.group(1))

    body = wikitext
    # 去掉 header2 模板块與 Textquality 標記；<BR> 視為換行（後期卷以此分段）
    body = re.sub(r"\{\{header2.*?\}\}", "", body, flags=re.S)
    body = re.sub(r"\{\{Textquality[^}]*\}\}", "", body)
    body = re.sub(r"<BR\s*/?>", "\n", body, flags=re.I)

    sections = []
    cur = {"level": 2, "heading": "（卷首）", "year_heading": None, "events": [], "comments": []}
    sections.append(cur)
    cur_year = None

    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        h = RE_HEADING.match(line)
        if h:
            level = len(h.group(1))
            text, _ = clean_inline(h.group(2))
            if level == 2:
                cur = {"level": 2, "heading": text, "year_heading": None, "events": [], "comments": []}
                sections.append(cur)
                cur_year = None
            else:
                # 年号標題（=== ... ===）
                cur_year = text
                cur["year_heading"] = text
            continue

        if line.startswith("::"):
            content = line.lstrip(":").strip()
            if content.startswith("臣光曰"):
                text, notes = clean_inline(content)
                cur["comments"].append({"text": text, "notes": notes, "year": cur_year})
            else:
                text, notes = clean_inline(content)
                if text:
                    cur["comments"].append({"text": text, "notes": notes, "year": cur_year, "kind": "note-or-quote"})
            continue

        em = RE_EVENT.match(line)
        if em:
            no = int(em.group(1))
            text, notes = clean_inline(em.group(2))
            cur["events"].append({"no": no, "year": cur_year, "text": text, "notes": notes})
            continue

        # 无 ''' 標記的年号行（後期卷），如 "孝宗穆皇帝…永和十一年（乙卯，公元三五五年）"
        plain, pnotes = clean_inline(line)
        if RE_PLAIN_YEAR.search(plain) and len(plain) < 80:
            cur_year = plain
            cur["year_heading"] = plain
            continue

        # 卷首"【…】起…盡…"與"資治通鑑 第N卷"：記為卷首，不計事件
        if plain.startswith("資治通鑑") or plain.startswith("【"):
            cur.setdefault("preface", []).append({"text": plain, "notes": pnotes})
            continue

        if not plain:
            continue

        # 臣光曰（无 :: 前缀的寫法）
        if plain.startswith("臣光曰"):
            cur["comments"].append({"text": plain, "notes": pnotes, "year": cur_year})
            continue

        # 其余段落視為事件（後期卷无編号）：編号按本节顺序递增
        cur["events"].append({"no": len(cur["events"]) + 1, "year": cur_year, "text": plain, "notes": pnotes})

    stats = {
        "sections": len(sections),
        "events": sum(len(s["events"]) for s in sections),
        "comments": sum(len(s["comments"]) for s in sections),
        "notes": sum(len(e["notes"]) for s in sections for e in s["events"]),
    }
    return {
        "juan": n,
        "title": section_title,
        "period": period,
        "sections": sections,
        "stats": stats,
    }


def main() -> int:
    os.makedirs(DATA, exist_ok=True)
    files = sorted(f for f in os.listdir(RAW) if re.match(r"juan\d{3}\.wiki$", f))
    if not files:
        print("no raw files; run fetch_wikisource.py first", file=sys.stderr)
        return 1
    index = []
    for f in files:
        n = int(f[4:7])
        with open(os.path.join(RAW, f), encoding="utf-8") as fh:
            wikitext = fh.read()
        obj = parse_juan(n, wikitext)
        out = os.path.join(DATA, f"juan{n:03d}.json")
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=2)
        index.append({"juan": n, "title": obj["title"], **obj["stats"]})
        print(f"[parsed] juan{n:03d} events={obj['stats']['events']} comments={obj['stats']['comments']}")
    with open(os.path.join(DATA, "_index.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(index, fh, ensure_ascii=False, indent=2)
    total_ev = sum(i["events"] for i in index)
    total_cm = sum(i["comments"] for i in index)
    print(f"juan={len(index)} events={total_ev} comments={total_cm}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
