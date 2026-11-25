# 歷史地圖整合（maps/）

本目錄負責《資治通鑑》地名與歷史地圖來源的對應，目前只做**連結層**。

## 檔案

| 檔案 | 說明 |
|---|---|
| `sources.md` | 各來源的名稱、網址、涵蓋時期、格式、授權摘錄、可否連結與可否保存派生資料 |
| `links.json` | 由 `scripts/build_map_links.py` 產生的地名與來源連結 |
| `README.md` | 本檔：整合策略、授權限制、待決定事項與執行記錄 |

重新產生：

```powershell
python scripts\build_map_links.py
```

腳本只讀取 `data/`（與地名清單檔），只寫入 `maps/links.json`，可重複執行，結果相同。

## 整合策略（連結層）

1. **不把受限資料放進儲存庫**。CHGIS 禁止再散布，Pitt 宋代資料為 CC BY-ND（禁止改作），Commons 檔案授權各異。
2. `links.json` 只記錄來源 URL、授權摘要與狀態。
3. 連結是**朝代層級**：卷標題的朝代（如「宋紀」）對應到該朝代可連結的來源。腳本未逐一驗證某個地名是否確實出現在來源資料中。
4. 授權不明確者一律標示 `待確認`，不自行假設可用。

## 地名清單來源

依優先順序讀取第一個存在的檔案：`--places` 指定檔 → `data/entities/places.json` → `data/entities/places_verified.json`（含主倉庫下的同名檔，因 `data/entities/` 為未追蹤檔）。全部不存在時才退回種子地名。

- 2026-11-25 目前使用 **`data/entities/places_verified.json`**（另一子工作階段產生，主倉庫中）。該檔共 3587 筆，其中 `rejected_noise`、`rejected_generic`、`rejected_manual` 共 2128 筆已排除，保留 1459 筆。
- 每個地名的 `verification` 欄沿用該檔的狀態：`confirmed_same_era`、`confirmed_other_era`、`confirmed_manual`、`phrase_resolved`（已確認）；`unverified`（624 筆）與 `regime_place_pending`（80 筆）未確認，使用時需注意。
- 其中 `西漢` 表為空（該檔自述「待補」），周秦漢地名以西漢表參照，結果需人工抽樣確認。
- `links.json` 中 `provisional: false`。只有「朝代」層級的連結：卷標題的朝代對應到該朝代可連結的來源。腳本未逐一驗證某個地名是否確實出現在來源資料中。
- 1459 筆中約 290 筆所在卷的朝代（如北魏、晉、隋、齊）沒有已驗證的開放來源，連結標為 `待確認`。
- 命中卷數是以事件文字做子字串比對，廣域地名（如「河南」）會偏高；這只代表文字出現次數，不代表地點精確性。
- 暫定種子清單（52 個）已於 2026-11-25 之前的版本使用，現僅在找不到任何地名檔時才會使用。

## 授權限制摘要

| 來源 | 限制 | 本專案做法 |
|---|---|---|
| CHGIS V6 | 僅限學術研究，禁止商業用途、轉售與再散布 | 只連結，不下載、不保存 |
| Pitt 宋代地名資料庫 | CC BY-ND 4.0：不得改作；派生資料（投影、轉格式、重建資料庫）不得公開散布 | 只連結，不下載、不保存 |
| Wikimedia Commons（SVG 歷史地圖） | 逐檔授權（CC0、CC BY-SA 等）；需逐檔確認 | 只連結分類與檔案頁；保存前須逐檔確認 |
| Commons：Atlas of PRC 分類 | 分類頁回 404，授權未知 | 待確認，不列為可用連結 |

另：維基文庫原文（`raw/`）為 CC BY-SA，與本資料夾無關，但若日後把地圖圖像與文本並列，需一併標示。

## 待使用者決定的事項

1. **是否改為保存派生資料？** 目前預設只連結。若要保存 Pitt 宋代資料的派生版本（如轉成 CSV 或 GeoJSON），需先取得作者許可，因為 CC BY-ND 不允許改作。
2. **是否下載 CHGIS 資料？** 授權禁止再散布。下載並存於儲存庫屬再散布，依任務規定需先回報詢問。目前未下載任何檔案。
3. **Commons 圖像要不要保存？** 需逐檔確認授權（CC0 與 CC BY-SA 的標示要求不同）。是否值得花時間逐檔整理，待決定。
4. **唐代行政區的來源**：目前無已驗證的開放來源，待確認。
5. **《中國歷史地圖集》**：未找到開放版本，待確認是否要以其他方式補足。
6. **CHGIS 的範圍與 Dataverse 條款**：頁面未載明朝代與年代範圍；Dataverse 資料集條款 2026-11-25 仍未取得（頁面回 HTTP 202 空內容），待確認。
7. **地名清單的歸屬**：目前讀取另一子工作階段的 `places_verified.json`（未追蹤檔）。該檔若更名或重做，需同步更新 `scripts/build_map_links.py` 的候選檔名，或以 `--places` 指定。

## 執行記錄

- 2026-11-24：首次驗證 CHGIS V6、Pitt 宋代地名資料庫、Wikimedia Commons（SVG 歷史地圖分類與抽查檔案）；Commons Atlas 分類頁回 404。新增 `scripts/build_map_links.py`，產生 52 個暫定地名的 `links.json`。
- 2026-11-25：再次驗證四個來源頁面（curl 抓原文）。授權字句與 11-24 相同；Commons 分類 119 檔、Atlas 分類仍 404；Dataverse 條款仍未取得。
- 2026-11-25：腳本改為讀取 `places_verified.json`（排除 rejected_*），輸出 1459 筆地名、`provisional: false`；連結改為精簡格式（來源細節集中於 `links.json` 的 `sources`）。重複執行結果相同（已以 `cmp` 確認）。
- 本次未下載任何 GIS 或圖像檔案，未修改 `raw/`、`data/juan*.json`、`data/entities/`、`web/`。
