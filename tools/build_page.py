# Build ../index.html from site.tpl.html + MapLibre CSS + data/data.json
from pathlib import Path
here = Path(__file__).parent
t = (here / "site.tpl.html").read_text()
t = t.replace("/*MAPLIBRE_CSS*/", (here / "maplibre.css").read_text()).replace("/*DATA*/", (here / "data" / "data.json").read_text())
(here.parent / "index.html").write_text(t)
print("index.html", len(t.encode()) // 1024, "KB")
