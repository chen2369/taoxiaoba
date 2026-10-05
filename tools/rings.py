import json
def assemble(ways):
    ways = [w[:] for w in ways if len(w) > 1]
    rings = []
    key = lambda p: (round(p[0], 7), round(p[1], 7))
    while ways:
        ring = ways.pop(0)
        changed = True
        while key(ring[0]) != key(ring[-1]) and changed:
            changed = False
            for i, w in enumerate(ways):
                if key(w[0]) == key(ring[-1]): ring += w[1:]
                elif key(w[-1]) == key(ring[-1]): ring += w[::-1][1:]
                elif key(w[-1]) == key(ring[0]): ring = w[:-1] + ring
                elif key(w[0]) == key(ring[0]): ring = w[::-1][:-1] + ring
                else: continue
                ways.pop(i); changed = True; break
        rings.append((ring, key(ring[0]) == key(ring[-1])))
    return rings
if __name__ == "__main__":
    for rel in json.load(open("admin.json"))["elements"]:
        outer = [[[g["lat"], g["lon"]] for g in m["geometry"]] for m in rel["members"] if m["type"] == "way" and m.get("role") == "outer"]
        rs = assemble(outer)
        pts = [p for r, _ in rs for p in r]
        print(rel["tags"]["name"], [(len(r), c) for r, c in rs], "lat", round(min(p[0] for p in pts), 3), round(max(p[0] for p in pts), 3), "lng", round(min(p[1] for p in pts), 3), round(max(p[1] for p in pts), 3))
