# 資治通鑑知識庫（zizhi-tongjian）

以《資治通鑑》全書 294 卷為對象，建立可檢索、可追溯的結構化知識庫。方法參考 [shiji-kb](https://github.com/baojie/shiji-kb)（《史記》知識庫）：先把古文變成結構化資料，再從資料產生索引與網頁。

## 目前進度

| 階段 | 內容 | 狀態 |
|---|---|---|
| 1. 取得原文 | 從維基文庫抓取 `資治通鑑/卷001`–`卷294` 的 wikitext | 進行中 |
| 2. 結構化解析 | 拆分卷、年號、編號事件、「臣光曰」論斷、校勘注 | 解析器已通過卷 001 測試 |
| 3. 實體與事件抽取 | 人物、地名、官職、年代 | 未開始 |
| 4. 網頁成品 | 全文瀏覽、檢索、時間線 | 未開始 |

## 目錄結構

```
raw/        維基文庫原始 wikitext（juanNNN.wiki），來源未經修改
data/       解析後的結構化 JSON（juanNNN.json）與 _index.json 總表
scripts/    fetch_wikisource.py（抓取）、parse_wikitext.py（解析）
整理日誌.md  每次執行的紀錄
```

## 重新產生資料

```powershell
python scripts\fetch_wikisource.py   # 抓取（已存在的檔案會跳過，可續抓）
python scripts\parse_wikitext.py     # 解析為 data/*.json
```

抓取約每秒 0.5 次請求，遇到限流會退避重試。

## 來源與授權

- 原文：《資治通鑑》為北宋司馬光編撰之古籍，原文屬公有領域。
- 文本來源：[維基文庫](https://zh.wikisource.org/wiki/資治通鑑)。維基文庫之文字採 CC BY-SA 授權，使用時請保留來源與授權。
- 本專案產生的結構化資料與程式碼授權待定，發布到 GitHub 前會再確認。

## 注意

- 原文校勘注（`〔…〕(…)` 與 `<ref>`）保留在 `notes` 欄位，不會被刪除。
- 解析結果依賴維基文庫的排版，若來源頁面有變動，需重新抓取與校對。
- 事件的年號來自最近一個年號標題，跨年的記載可能需要人工校正。

## 歷史地名對照與 CHGIS 引用

本專案的歷代地名表主要取自維基文庫上的正史地理志（公有領域），見 `scripts/build_gazetteer.py`。

部分地名的朝代歸屬與行政層級對照，參考了哈佛大學 Fairbank Center 與復旦大學歷史地理研究中心合作的 **China Historical GIS（CHGIS）Version 6**。標準引用如下：

> CHGIS, Version 6. (c) Fairbank Center for Chinese Studies of Harvard University and the Center for Historical Geographical Studies at Fudan University, 2016.

使用說明：

- 本專案只公開統計結論、方法說明與少量示例；逐條對照結果僅保存於本機，不隨儲存庫發布。
- 本專案不包含 CHGIS 的原始資料或其整體衍生資料集。
- 使用範圍為非商業的學術研究與教育。若需商業用途或完整資料，應依 CHGIS 授權條款另行取得許可。
- 本專案對 CHGIS 資料所做的修改：僅取用地名與朝代對應，未修改其原始座標與行政層級。

## 政權地名查證結論（依 CHGIS 查證）

以下為《資治通鑑》中「政權＋州名」的現代地點結論，依 CHGIS 查證（僅列結論，不含資料庫記錄）。政權欄標明是否已由 CHGIS 父級政權確認。

| 原文名稱 | 政權 | 政權是否確認 | 現代地點 |
|---|---|---|---|
| 魏幽州 | 北魏 | 否（CHGIS 父級為後趙） | 北京西南（廣安門、豐台一帶） |
| 秦梁州 | 前秦 | 否（記錄無父級） | 陝西漢中一帶 |
| 劉兗州 | 劉宋 | 是 | 早期（約 438–443 年）寄治於徐州（彭城）一帶；約 453 年起為今山東兗州 |
| 燕幽州 | 前燕 | 否（CHGIS 父級為後趙，未見前燕記錄） | 北京西南（廣安門、豐台一帶） |
| 齊揚州 | 南齊 | 否（CHGIS 父級為南朝宋） | 南京 |
| 周徐州 | 北周 | 否（記錄無父級） | 江蘇徐州 |
| 唐濠州 | 唐 | 年份涵蓋唐代 | 安徽鳳陽一帶 |
| 前幽州 | 待判定（前朝） | 否 | 北京西南（廣安門、豐台一帶） |

**注意**：同一州名在不同政權下，地點與轄區可能不同，不應合併為同一地點。

引用：CHGIS, Version 6. (c) Fairbank Center for Chinese Studies of Harvard University and the Center for Historical Geographical Studies at Fudan University, 2016.
