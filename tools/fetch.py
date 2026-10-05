import json, time, urllib.request, subprocess
API = "https://ebus.tycg.gov.tw/ebus/graphql"

def gql(query, variables):
    body = json.dumps({"query": query, "variables": variables})
    for attempt in range(3):
        out = subprocess.run(["curl", "-s", "-m", "60", API, "-H", "Content-Type: application/json", "-d", body],
                             capture_output=True, text=True).stdout
        try:
            d = json.loads(out)
            if "data" in d and d["data"] is not None:
                return d["data"]
        except Exception:
            pass
        time.sleep(2)
    raise RuntimeError(f"failed {variables}: {out[:200]}")

def decode_polyline(s):
    coords, i, lat, lng = [], 0, 0, 0
    while i < len(s):
        for which in (0, 1):
            shift = result = 0
            while True:
                b = ord(s[i]) - 63; i += 1
                result |= (b & 0x1f) << shift; shift += 5
                if b < 0x20: break
            delta = ~(result >> 1) if result & 1 else result >> 1
            if which == 0: lat += delta
            else: lng += delta
        coords.append([round(lat / 1e5, 5), round(lng / 1e5, 5)])
    return coords

routes = [x["node"] for x in json.load(open("data/allroutes.json"))["data"]["routes"]["edges"]]
small = [r for r in routes if r["opType"] == 10]

DISTRICTS = ["桃園區","中壢區","平鎮區","八德區","楊梅區","蘆竹區","大溪區","龍潭區","龜山區","大園區","觀音區","新屋區","復興區"]
town_of = {}
for t in DISTRICTS:
    d = gql("query($t:String!,$lang:String!){routesByTown(town:$t,lang:$lang){edges{node{id}}}}", {"t": t, "lang": "zh"})
    for e in d["routesByTown"]["edges"]:
        town_of.setdefault(str(e["node"]["id"]), set()).add(t)
    time.sleep(0.2)

DETAIL = """query($id:Int!,$lang:String!){route(xno:$id,lang:$lang){id name departure destination description
 providers{edges{node{name telephone}}} routePoint{go back}
 stations{edges{goBack orderNo node{id name lat lon}}}}}"""
TT = """query($id:Int!,$date:String){dailySchedule(xno:$id,date:$date){__typename
 ... on DailyTimeTableConnection{edges{node{goBack scheduleTime}}}
 ... on DailyHeadwayConnection{edges{node{goBack startTime endTime upperLimit lowerLimit}}}}}"""

def sched(rid, date):
    d = gql(TT, {"id": int(rid), "date": date})["dailySchedule"]
    if not d: return None
    res = {"1": [], "2": []}
    if d["__typename"] == "DailyTimeTableConnection":
        for e in d["edges"]:
            res[str(e["node"]["goBack"])].append(e["node"]["scheduleTime"])
        for k in res: res[k] = sorted(set(res[k]))
    else:
        for e in d["edges"]:
            n = e["node"]
            res[str(n["goBack"])].append(f'{n["startTime"]}-{n["endTime"]} 每{n["lowerLimit"]}~{n["upperLimit"]}分')
    return res

out = []
for r in small:
    rid = r["id"]
    d = gql(DETAIL, {"id": int(rid), "lang": "zh"})["route"]
    stops = {"1": [], "2": []}
    for e in sorted(d["stations"]["edges"], key=lambda e: (e["goBack"], e["orderNo"])):
        n = e["node"]
        stops[str(e["goBack"])].append([n["name"], round(n["lat"], 6), round(n["lon"], 6), int(n["id"])])
    rp = d.get("routePoint") or {}
    name = d["name"]
    cat = "T" if name.upper().startswith("T") else ("F" if name.upper().startswith("F") else "O")
    out.append({
        "id": rid, "name": name, "desc": d["description"], "dep": d["departure"], "dest": d["destination"],
        "cat": cat,
        "towns": sorted(town_of.get(rid, [])),
        "op": ", ".join(p["node"]["name"] for p in d["providers"]["edges"]),
        "tel": ", ".join(p["node"]["telephone"] or "" for p in d["providers"]["edges"]),
        "shape": {"1": decode_polyline(rp["go"]) if rp.get("go") else [],
                  "2": decode_polyline(rp["back"]) if rp.get("back") else []},
        "stops": stops,
        "wk": sched(rid, "2026-10-07"),
        "we": sched(rid, "2026-10-11"),
    })
    print(name, len(out[-1]["shape"]["1"]), len(out[-1]["shape"]["2"]), len(stops["1"]), len(stops["2"]), out[-1]["towns"], flush=True)
    time.sleep(0.2)

json.dump(out, open("data/smallbus.json", "w"), ensure_ascii=False, separators=(",", ":"))
print("done", len(out))
