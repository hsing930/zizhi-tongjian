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
