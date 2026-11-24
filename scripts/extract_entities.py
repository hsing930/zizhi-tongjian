# -*- coding: utf-8 -*-
"""
從 data/juanNNN.json 抽取實體（人物、地名、官職），輸出到 data/entities/。

方法（詞典＋規則，無外部 NLP/LLM）：
- 官職：內建常見官稱詞典，計算每個官稱在各事件/臣光曰中的出現。
- 地名：內建常見州郡、都城、關隘、山川詞典（含別稱），加上「X州/郡/縣/關」等後綴規則；
  後綴規則得到的結果列為待確認。
- 人物：以百家姓常見姓氏（含複姓）＋1–2 字名，出現在引語、動詞前後的語境中，
  出現 >= MIN_AUTO 次者進 people.json，少於者進 _review.json。
- 所有實體記錄首見卷/年號，以及所有出現位置 (juan, event no, year)。

執行：python scripts/extract_entities.py   （於專案根目錄執行）
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "entities"

MIN_AUTO = 2          # 人物：出現次數達此值才自動收錄
MIN_REVIEW = 1        # 人物：達此值但未達 MIN_AUTO 進待確認

# ---------- 官職詞典 ----------
OFFICES = {
    "丞相": [], "相國": [], "太尉": ["大尉"], "司徒": [], "司空": [], "太傅": ["太傅"],
    "太師": [], "太保": [], "大司馬": [], "大司徒": [], "大司空": [], "大司寇": [],
    "司馬": [], "司寇": [], "司空": [], "冢宰": [], "宰相": [], "令尹": [], "上柱國": [],
    "御史大夫": [], "御史中丞": [], "御史": [], "大將軍": [], "將軍": [], "車騎將軍": [],
    "驃騎將軍": [], "衛將軍": [], "左將軍": [], "右將軍": [], "中郎將": [], "校尉": [],
    "都督": [], "都尉": [], "刺史": [], "太守": [], "郡守": [], "縣令": [], "縣尉": [],
    "節度使": [], "觀察使": [], "防禦使": [], "經略使": [], "宣撫使": [], "樞密使": [],
    "中書令": [], "中書侍郎": [], "中書舍人": [], "侍中": [], "給事中": [], "尚書令": [],
    "尚書僕射": ["僕射"], "尚書": [], "左僕射": [], "右僕射": [], "門下侍郎": [],
    "散騎常侍": [], "散騎": [], "太子太傅": [], "太子少傅": [], "太常": [], "太僕": [],
    "廷尉": [], "大理": [], "光祿勳": [], "衛尉": [], "太史": [], "博士": [], "祭酒": [],
    "諫議大夫": [], "諫大夫": [], "大夫": [], "上大夫": [], "中大夫": [], "郎中": [],
    "侍郎": [], "舍人": [], "長史": [], "別駕": [], "參軍": [], "主簿": [], "司馬": [],
    "將作大匠": [], "少府": [], "大司農": [], "司農": [], "鴻臚": [], "典客": [],
    "內史": [], "郎": [], "謁者": [], "黃門": [], "宦官": [], "中常侍": [], "常侍": [],
    "太宰": [], "宰": [], "縣丞": [], "縣長": [], "縣侯": [], "列侯": [], "王侯": [],
    "諸侯": [], "方伯": [], "牧": [], "州牧": [], "刺客": [],
    "天子": [], "皇帝": [], "太子": [], "皇后": [], "太后": [], "皇太子": [],
    "藩鎮": [], "節帥": [], "監軍": [], "節鎮": [], "都護": [], "校": [],
}
# 把「別名→標準名」轉為統一表
OFFICE_ALIAS = {}
for std, aliases in OFFICES.items():
    OFFICE_ALIAS[std] = std
    for a in aliases:
        OFFICE_ALIAS[a] = std

# ---------- 地名詞典（標準名 → 別稱） ----------
PLACES = {
    "長安": ["西京"], "洛陽": ["洛邑", "雒陽", "東都", "河南"], "建康": ["金陵", "建業", "江寧"],
    "襄陽": ["襄陽城"], "江陵": ["荊州"], "成都": ["益州"], "鄴": ["鄴城"], "汴州": ["汴京", "汴梁", "大梁"],
    "開封": ["東京"], "幽州": ["薊"], "并州": ["太原"], "涼州": ["姑臧"], "揚州": ["廣陵"],
    "廣陵": ["邗"], "彭城": ["徐州"], "會稽": ["越"], "吳": ["姑蘇", "吳郡"], "楚": ["荊"],
    "燕": ["薊"], "趙": ["邯鄲"], "魏": ["大梁"], "韓": ["新鄭"], "齊": ["臨淄"], "秦": ["咸陽"],
    "晉陽": ["晉陽城"], "蜀": ["漢中", "益州"], "南郡": [], "關中": ["三輔"], "河北": ["河朔"],
    "河南": ["中原"], "江南": ["江左", "江東"], "江北": ["江左", "淮北"], "淮南": ["淮左"],
    "巴蜀": ["蜀中", "西蜀"], "隴右": ["隴西"], "漠北": ["大漠"], "嶺南": ["嶺表"],
    "黃河": ["河", "大河"], "長江": ["江", "大江"], "淮河": ["淮", "淮水"], "洛水": ["洛"],
    "渭水": ["渭"], "汴河": ["汴水"], "太行山": ["太行"], "崤山": ["崤"], "函谷關": ["函谷"],
    "潼關": ["潼"], "虎牢": ["虎牢關"], "雁門": ["雁門關"], "玉門關": ["玉門"],
    "雍州": [], "冀州": [], "青州": [], "兗州": [], "豫州": [], "荊州": [], "徐州": [], "梁州": [],
    "交州": [], "益州": [], "并州": [], "幽州": [],
    "蔡州": [], "淮西": [], "河東": [], "河西": [], "隴西": [], "朔方": [], "幽燕": [], "燕雲": [],
    "嶺外": [], "荊襄": [], "吳越": [], "齊魯": [], "宋州": [], "滑州": [],
}
PLACE_ALIAS = {}
for std, aliases in PLACES.items():
    PLACE_ALIAS[std] = std
    for a in aliases:
        PLACE_ALIAS.setdefault(a, std)
# 地名後綴規則：「X州/郡/縣/關/山/河」，結果列待確認
PLACE_SUFFIX_RE = re.compile(r"([一-鿿]{1,2})(州|郡|縣|關|城|山|河|水)")
PLACE_STOP_PREFIX = set("諸各此其之以於與及有是無為所等至皆又自從東西南北中上下大小")

# ---------- 人物：姓氏 ----------
SURNAMES = list(dict.fromkeys(
    "趙 錢 孫 李 周 吳 鄭 王 馮 陳 褚 衛 蔣 沈 韓 楊 朱 秦 尤 許 何 呂 施 張 孔 曹 嚴 華 金 魏 陶 姜 "
    "戚 謝 鄒 喻 柏 水 竇 章 雲 蘇 潘 葛 奚 范 彭 郎 魯 韋 昌 馬 苗 鳳 花 方 俞 任 袁 柳 酆 鮑 史 唐 "
    "費 廉 岑 薛 雷 賀 倪 湯 滕 殷 羅 畢 郝 鄔 安 常 樂 於 時 傅 皮 卞 齊 康 伍 餘 元 卜 顧 孟 平 黃 "
    "和 穆 蕭 尹 姚 邵 湛 汪 祁 毛 禹 狄 米 貝 明 臧 計 伏 成 戴 談 宋 茅 龐 熊 紀 舒 屈 項 祝 董 梁 "
    "杜 阮 藍 閔 席 季 麻 強 賈 路 婁 危 江 童 顏 郭 梅 盛 林 刁 鍾 徐 邱 駱 高 夏 蔡 田 樊 胡 凌 霍 "
    "虞 萬 支 柯 昝 管 盧 莫 經 房 裘 繆 干 解 應 宗 丁 宣 賁 鄧 郁 單 杭 洪 包 諸葛 司馬 歐陽 上官 "
    "公孫 慕容 獨孤 宇文 長孫 皇甫 尉遲 令狐 夏侯 公羊 東方 鮮于 呼延 南宮 百里 申屠 漆雕 拓跋 "
    "贏 嬴 姬 姒 媯 姞 嬀 芈 隗 郤 蒯 鮮 卓 宓 甯 寧 聶 晏 陽 冉 辛 奉 巢 遊 壽 劉 高 呂 項 曲 "
    "蘭 仲 孫 叔 季 伯 白 辛 公 侯 歸 厙 易 翟 步 宿 溫 仇 聶 祖 郗 向 兀 富 烏 劉".split()
))
# 單字姓氏（去掉多字項）
# 這些單字同時是常見副詞／動詞（「莫敢」「何足」「安得」），作為姓氏會大量誤判，故排除
SURNAME_STOP = set("莫何安奉平於時和單寧將令公侯向常方富水成明陽白")
SURNAMES = [s for s in SURNAMES if s not in SURNAME_STOP]
SURNAMES_1 = sorted({s for s in SURNAMES if len(s) == 1}, key=len)
SURNAMES_2 = sorted({s for s in SURNAMES if len(s) == 2}, key=len, reverse=True)

# 名字第二字不應為這些字（常見虛詞／動詞），用來減少誤判
NAME_BAD = set("之以為與及將曰也者而於則所有不無是其來去出入上下中在自大小可必不乃又已皆既乃遂使令請拜召")
# 名字首字若為這些字，多半是「魏主」「時人」「公卿」之類稱謂而非人名，直接排除
ROLE_HEAD = set("主人卿王公帝后臣民軍吏卒兵眾氏下君官使女妃夫翁家將相侯師大太令書事志")
# 名字後必須接的語境字（引語、動詞）；只有這樣的命中才計入人名，減少誤判
CONTEXT_CHARS = set("曰謂言以為與及將召請拜遣使敗殺奔入至還聞問率帥執走降薨卒立說乃從")

# ---------- 文本前處理 ----------
WIKI_LANG_RE = re.compile(r"-\{(.*?)\}-", re.S)   # 語言轉換：-{於}- → 於
NOTE_RE = re.compile(r"〔[^〕]*〕")               # 〔校勘注〕保留？此處僅用於比對前去掉


def clean_text(s: str) -> str:
    s = WIKI_LANG_RE.sub(lambda m: m.group(1), s)
    s = s.replace("〔", "").replace("〕", "")
    return s


def iter_units(juan_obj):
    """產生 (juan, year, event_no, text)；事件與臣光曰皆視為單元。event_no 為 None 表示臣光曰。"""
    juan = juan_obj["juan"]
    for sec in juan_obj.get("sections", []):
        year_name = None
        if sec.get("year_heading"):
            year_name = sec["year_heading"]
        for ev in sec.get("events", []):
            y = ev.get("year") or year_name
            yield juan, y, ev.get("no"), clean_text(ev.get("text", ""))
        for c in sec.get("comments", []):
            txt = c.get("text", "") if isinstance(c, dict) else str(c)
            yield juan, year_name, None, clean_text(txt)


def load_juans():
    juans = []
    for p in sorted(DATA.glob("juan*.json")):
        with open(p, encoding="utf-8") as f:
            juans.append(json.load(f))
    return juans


def build_name_regex():
    """姓 + 1–2 字名，且名後必須接語境字（曰、為、與…），以降低誤判。
    先試 2 字名，再試 1 字名（regex 會依序嘗試）。"""
    surn = "|".join(re.escape(s) for s in SURNAMES_2 + SURNAMES_1)
    ctx = "".join(sorted(CONTEXT_CHARS))
    return re.compile(
        rf"(?<![一-鿿])({surn})([一-鿿]{{2}}|[一-鿿])(?=[{ctx}])"
    )


def extract_people(units):
    name_re = build_name_regex()
    occ = defaultdict(list)     # 形式 → [(juan, year, no)]
    for juan, year, no, text in units:
        for m in name_re.finditer(text):
            surname, given = m.group(1), m.group(2)
            if any(c in NAME_BAD for c in given) or given[0] in ROLE_HEAD:
                continue
            occ[surname + given].append((juan, year, no))
    return occ


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    juans = load_juans()
    if not juans:
        print("找不到 data/juan*.json，請先執行 parse_wikitext.py", file=sys.stderr)
        sys.exit(1)
    units = []
    for j in juans:
        units.extend(iter_units(j))
    print(f"卷數 {len(juans)}，單元 {len(units)}")

    # ---------- 官職 ----------
    office_keys = sorted(OFFICE_ALIAS.keys(), key=len, reverse=True)
    office_re = re.compile("|".join(re.escape(k) for k in office_keys))
    off_occ = defaultdict(list)
    for juan, year, no, text in units:
        for m in office_re.finditer(text):
            off_occ[OFFICE_ALIAS[m.group(0)]].append((juan, year, no))

    # ---------- 地名 ----------
    place_keys = sorted(PLACE_ALIAS.keys(), key=len, reverse=True)
    place_re = re.compile("|".join(re.escape(k) for k in place_keys))
    pl_occ = defaultdict(list)
    pl_review = defaultdict(list)
    for juan, year, no, text in units:
        for m in place_re.finditer(text):
            pl_occ[PLACE_ALIAS[m.group(0)]].append((juan, year, no))
        for m in PLACE_SUFFIX_RE.finditer(text):
            pre, suf = m.group(1), m.group(2)
            if pre[0] in PLACE_STOP_PREFIX or pre in PLACE_ALIAS:
                continue
            pl_review[pre + suf].append((juan, year, no))

    # ---------- 人物 ----------
    occ = extract_people(units)

    def record(name, rows, extra=None):
        rows = sorted(rows, key=lambda r: (r[0], r[2] if r[2] is not None else 10**6))
        first = rows[0]
        rec = {
            "id": None,
            "name": name,
            "aliases": [],
            "first_juan": first[0],
            "first_year": first[1],
            "count": len(rows),
            "occurrences": [{"juan": j, "year": y, "event_no": n} for j, y, n in rows],
            "juans": sorted({r[0] for r in rows}),
        }
        if extra:
            rec.update(extra)
        return rec

    def assign_ids(records, prefix):
        for i, r in enumerate(records, 1):
            r["id"] = f"{prefix}{i:05d}"
        return records

    # 人物分組：自動 / 待確認
    people_auto, people_review = [], []
    for name, rows in occ.items():
        cnt = len(rows)
        if cnt >= MIN_AUTO:
            people_auto.append(record(name, rows, {"confidence": "auto"}))
        elif cnt >= MIN_REVIEW:
            people_review.append({"kind": "person", "name": name, "count": cnt,
                                  "reason": "出現次數未達自動收錄門檻，需人工確認是否為人名",
                                  "first_juan": min(r[0] for r in rows)})
    people_auto.sort(key=lambda r: -r["count"])
    assign_ids(people_auto, "P")

    offices = [record(k, v) for k, v in off_occ.items() if len(v) > 0]
    offices.sort(key=lambda r: -r["count"])
    assign_ids(offices, "O")

    places_auto = [record(k, v) for k, v in pl_occ.items()]
    places_auto.sort(key=lambda r: -r["count"])
    assign_ids(places_auto, "L")

    review = list(people_review)
    for k, v in pl_review.items():
        if len(v) >= 2:
            review.append({"kind": "place", "name": k, "count": len(v),
                           "reason": "後綴規則推得，未在詞典中，需人工確認",
                           "first_juan": min(r[0] for r in v)})
    review.sort(key=lambda r: (-r["count"], r["name"]))

    def write(name, obj):
        with open(OUT / name, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)

    write("people.json", people_auto)
    write("places.json", places_auto)
    write("offices.json", offices)
    write("_review.json", review)

    # ---------- 摘要 ----------
    per_juan = Counter()
    for name, lst in [("people", people_auto), ("places", places_auto), ("offices", offices)]:
        for r in lst:
            for j in r["juans"]:
                per_juan[(name, j)] += 1
    summary = {
        "counts": {
            "people": len(people_auto),
            "places": len(places_auto),
            "offices": len(offices),
            "review": len(review),
        },
        "per_juan": {
            str(j): {
                "people": per_juan[("people", j)],
                "places": per_juan[("places", j)],
                "offices": per_juan[("offices", j)],
            } for j in sorted({j["juan"] for j in juans})
        },
        "params": {"MIN_AUTO": MIN_AUTO, "MIN_REVIEW": MIN_REVIEW},
    }
    write("_summary.json", summary)
    print("完成：", summary["counts"])


if __name__ == "__main__":
    main()
