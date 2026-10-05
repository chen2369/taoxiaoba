import json, math

def dp(pts, tol):
    # Douglas-Peucker on [lat,lng] using local planar approximation
    if len(pts) < 3: return pts
    k = math.cos(math.radians(24.9))
    def d(p, a, b):
        ax, ay = a[1]*k, a[0]; bx, by = b[1]*k, b[0]; px, py = p[1]*k, p[0]
        dx, dy = bx-ax, by-ay
        if dx == dy == 0: return math.hypot(px-ax, py-ay)
        t = max(0, min(1, ((px-ax)*dx+(py-ay)*dy)/(dx*dx+dy*dy)))
        return math.hypot(px-(ax+t*dx), py-(ay+t*dy))
    keep = [False]*len(pts); keep[0] = keep[-1] = True
    stack = [(0, len(pts)-1)]
    while stack:
        i, j = stack.pop()
        best, idx = 0, -1
        for m in range(i+1, j):
            v = d(pts[m], pts[i], pts[j])
            if v > best: best, idx = v, m
        if best > tol:
            keep[idx] = True; stack += [(i, idx), (idx, j)]
    return [p for p, kp in zip(pts, keep) if kp]

def enc(pts):
    out, plat, plng = [], 0, 0
    for lat, lng in pts:
        ilat, ilng = round(lat*1e5), round(lng*1e5)
        for v in (ilat-plat, ilng-plng):
            v = ~(v << 1) if v < 0 else v << 1
            while v >= 0x20:
                out.append(chr((0x20 | (v & 0x1f)) + 63)); v >>= 5
            out.append(chr(v + 63))
        plat, plng = ilat, ilng
    return "".join(out)

M = 1/111000  # degrees per metre (lat)

# --- basemap
from rings import assemble
import collections
admin = json.load(open("data/admin.json"))["elements"]
seen, borders, labels = set(), [], []
ways, uses = {}, collections.Counter()
for rel in admin:
    for m in rel["members"]:
        if m["type"] != "way" or "geometry" not in m: continue
        if m.get("role") == "outer":
            uses[m["ref"]] += 1; ways[m["ref"]] = [[g["lat"], g["lon"]] for g in m["geometry"]]
        if m["ref"] in seen: continue
        seen.add(m["ref"])
        borders.append(enc(dp([[g["lat"], g["lon"]] for g in m["geometry"]], 25*M)))
    outer = [[[g["lat"], g["lon"]] for g in m["geometry"]] for m in rel["members"] if m["type"] == "way" and m.get("role") == "outer"]
    r = max((r for r, closed in assemble(outer)), key=len); A = cx = cy = 0
    for (y0, x0), (y1, x1) in zip(r, r[1:] + r[:1]):
        c = x0*y1 - x1*y0; A += c; cx += (x0+x1)*c; cy += (y0+y1)*c
    labels.append([rel["tags"]["name"], round(cy/(3*A), 4), round(cx/(3*A), 4)])
# city outline = district boundary ways used by only one district
outline = [enc(dp(r, 25*M)) for r, closed in assemble([w for ref, w in ways.items() if uses[ref] == 1]) if closed]
print("outline rings", len(outline))

lines = json.load(open("data/lines.json"))["elements"]
roads = {"motorway": [], "trunk": [], "primary": [], "secondary": []}
rail, metro, stations = [], [], {}
for e in lines:
    t = e.get("tags", {})
    if e["type"] == "node": continue
    pts = [[g["lat"], g["lon"]] for g in e["geometry"]]
    hw, rw = t.get("highway"), t.get("railway")
    if hw: roads[hw].append(enc(dp(pts, 12*M)))
    elif rw == "rail": rail.append(enc(dp(pts, 12*M)))
    else: metro.append(enc(dp(pts, 12*M)))

stations = []
for e in json.load(open("data/st.json"))["elements"]:
    t = e["tags"]; net = t.get("network", "")
    if not (24.80 < e["lat"] < 25.10 and 121.00 < e["lon"] < 121.40): continue
    kind = {"臺鐵": "tra", "台灣高鐵": "hsr", "桃園機場捷運": "mrt", "桃園捷運": "mrt"}.get(net)
    if not kind or t["name"] in ("竹北", "湖口", "千甲", "六家", "山佳"): continue
    if kind == "hsr" and t["name"] != "桃園": continue  # 高鐵新竹站 sits inside the bbox
    nm = t["name"] + ("站" if kind == "tra" else "") if kind != "mrt" else "捷運" + t["name"]
    if kind == "hsr" or t["name"] == "高鐵桃園站": nm = "高鐵桃園站"; kind = "hsr"
    if any(abs(x[1]-e["lat"]) < 0.003 and abs(x[2]-e["lon"]) < 0.003 for x in stations): continue
    stations.append([nm, round(e["lat"], 5), round(e["lon"], 5), kind])

# --- routes
routes = json.load(open("data/smallbus.json"))
CONFIRMED = {"5083", "5084", "5085", "5028"}  # news-confirmed 桃小巴 conversions keeping old numbers
R = []
for r in routes:
    cat = r["cat"]
    if cat == "O" and r["name"] in CONFIRMED: cat = "T"
    R.append({
        "id": r["id"], "n": r["name"], "d": r["desc"], "a": r["dep"], "b": r["dest"],
        "c": cat, "tw": [t[:-1] for t in r["towns"]], "op": r["op"], "tel": r["tel"],
        "s": [enc(dp(r["shape"][k], 4*M)) if r["shape"][k] else "" for k in ("1", "2")],
        "st": [[[n, la, lo, sid] for n, la, lo, sid in r["stops"][k]] for k in ("1", "2")],
        "wk": [r["wk"][k] if r["wk"] else [] for k in ("1", "2")],
        "we": [r["we"][k] if r["we"] else [] for k in ("1", "2")],
    })

data = {"base": {"outline": outline, "borders": borders, "labels": labels, "roads": roads, "rail": rail, "metro": metro, "stations": stations}, "routes": R}
s = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
open("data/data.json", "w").write(s)
print(len(s.encode()) // 1024, "KB;", "stations", len(stations), "routes", len(R), {c: sum(1 for x in R if x["c"] == c) for c in "TOF"})
