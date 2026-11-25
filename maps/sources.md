# 歷史地圖來源目錄

驗證日期：2026-11-24 首次驗證；**2026-11-25 再次驗證**（以 curl 抓取頁面原文，比對授權字句）。授權文字為頁面所載，若與搜尋摘要不一致，以頁面為準。2026-11-25 結果：CHGIS、Pitt、Commons 分類頁與抽查檔案皆 HTTP 200 且授權字句相同；Commons Atlas 分類頁仍 HTTP 404；Harvard Dataverse 資料集條款仍未取得（見下）。

| 名稱 | 網址 | 涵蓋時期 | 格式 | 授權（頁面原文摘錄） | 可否連結 | 可否保存派生資料 |
|---|---|---|---|---|---|---|
| CHGIS V6（哈佛 Fairbank Center / 復旦 CHGIS） | https://chgis.fas.harvard.edu/data/chgis/v6/ | 頁面未載明朝代與年代範圍（待確認）；版本內含 Time Series 與 1820/1911/1990 時間切片 | 頁面未註明格式；下載連結位於 Harvard Dataverse（https://dataverse.harvard.edu/dataverse/chgis_v6，未讀取） | "License: free for academic research, no commercial use, resale, or redistribution permitted." | 是（官方頁面） | 否（頁面禁止再散布；衍生作品未說明，依保守解讀不保存） |
| The Digital Gazetteer of the Song Dynasty（Meeks & Mostern，匹茲堡大學） | https://d-scholarship.pitt.edu/44108/ | 宋，頁面標示 0960–1276（摘要寫 906–1276，兩者不一致） | PDF；dgsd11.zip（MySQL）；dgsd11_access.zip（Access）；images.zip；DGSDshapefiles.zip（派生 shapefile） | "Creative Commons BY-ND Attribution-NoDerivatives 4.0 International" | 是 | 否：ND 禁止改作。重新投影、轉格式或以其建立新資料庫，屬改作，未經授權不得公開散布 |
| Wikimedia Commons：Category:SVG maps of the history of China | https://commons.wikimedia.org/wiki/Category:SVG_maps_of_the_history_of_China | 戰國、漢、唐等章節地圖（逐檔不同；分類頁載 119 檔） | SVG | 逐檔不同。已抽查：742nian_Tang.svg 為 "CC0 1.0 Universal Public Domain Dedication"；China_-_Song_Dynasty-mk.svg 為 "CC BY-SA 4.0"；Nanyue.svg 為 CC BY-SA 3.0 等多重授權 | 是（連結分類與個別檔案頁） | 待確認：須逐檔確認授權，CC BY-SA 需標示與同授權釋出 |
| Wikimedia Commons：Category:Atlas_of_the_People's_Republic_of_China | https://commons.wikimedia.org/wiki/Category:Atlas_of_the_People%27s_Republic_of_China | 未確認 | 未確認 | 驗證時回 HTTP 404，無法讀取授權 | **待確認**（不列為可用連結） | **待確認** |

## 未找到可用來源

- **譚其驤《中國歷史地圖集》**：未找到開放電子版。PRC Atlas 相關分類頁回 404，不以之作為來源。
- **唐代行政區**：缺少現成開放資料。CHGIS 可能涵蓋唐代，但頁面未載明範圍，且有禁止再散布條款，因此唐代行政區目前標為「待確認」，不硬連結。
- **Harvard Dataverse 的 CHGIS 條款頁**（https://dataverse.harvard.edu/dataverse/chgis_v6）：2026-11-25 兩次請求皆回 HTTP 202 空內容；其 API（/api/dataverses/chgis_v6）只回傳版本中繼資料，未含資料集授權。逐資料集條款**待確認**。在確認前，視 CHGIS 為「只連結、不下載、不保存」。

## 與先前搜尋摘要的差異

- CHGIS 搜尋摘要曾暗示可再利用，但頁面明載「no commercial use, resale, or redistribution permitted」。以頁面為準：只連結，不保存。
- Pitt 宋代資料的年代，頁面標示 0960–1276，摘要寫 906–1276。以頁面標示為準，兩者需在後續使用時再確認。
- Pitt 頁面另載「Copyright Not Evaluated」，並說明資料主要取自 Hope Wright 的 *An Alphabetical List of Geographical Names in Song China* 索引。此為上游來源的權利說明，未經評估；ND 條款已足以阻止改作與再散布，本專案不另處理。
- Commons 分類摘要列出的部分檔名（如 Xia dynasty.svg、Qin dynasty territory.svg）未在頁面文字中確認，視為未驗證。
