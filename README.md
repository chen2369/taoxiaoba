# 桃小巴路線圖

桃園市桃小巴（九人座小巴）路線地圖：路線軌跡、站牌、平日／假日班表，加上即時公車位置與預估到站時間。

網址：https://chen2369.github.io/taoxiaoba/

## 功能

- 地圖上畫出 95 條「桃小巴／幸福巴士」路線與所有站牌，可依類別、行政區、路線或站名篩選
- 點路線：去返程軌跡、停靠站、起點發車時刻，以及即時公車位置與每站預估到站時間
- 點站牌：經過該站的路線各用一色亮起，列出每條路線多久到站
- 即時資料選路線或點站牌後每 20 秒更新，頁面切到背景時暫停

## 資料來源

| 資料 | 來源 | 授權 |
|---|---|---|
| 路線、站牌、班表、即時動態 | 桃園市公車動態資訊系統 `https://ebus.tycg.gov.tw/ebus/graphql` | 政府公開資料 |
| 底圖（道路、路名、地標） | OpenStreetMap，經 Protomaps 每日 build 裁切 | ODbL |
| 行政區界、鐵路、車站 | OpenStreetMap（Overpass API） | ODbL |

## 更新資料

所有指令在 `tools/` 下執行。

```bash
# 1. 全市路線清單
curl -s https://ebus.tycg.gov.tw/ebus/graphql -H 'Content-Type: application/json' \
  -d '{"query":"query($lang:String!){routes(lang:$lang){edges{node{id seq name opType routeGroup description departure destination}}}}","variables":{"lang":"zh"}}' \
  > data/allroutes.json
# 2. 小巴路線細節（軌跡、站牌、班表）→ data/smallbus.json
python3 fetch.py
# 3. 整理成頁面用的資料 → data/data.json
python3 build.py
# 4. 產生 ../index.html
python3 build_page.py
```

`fetch.py` 裡班表抓取的日期（一個平日、一個週日），和 `site.tpl.html` 的 `FETCHED` 日期，更新時要一起改。

底圖更新（需要 [go-pmtiles](https://github.com/protomaps/go-pmtiles)）：

```bash
pmtiles extract https://build.protomaps.com/<YYYYMMDD>.pmtiles ../basemap.pmtiles \
  --region=data/taoyuan.geojson --maxzoom=14
```
