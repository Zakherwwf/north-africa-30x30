"""Per-site shapes for the clickable country map (WWF dashboard).

For each country, reads the counted sites as saved by 01_gis_flatten.py (buffered points included, Mollweide),
clips them to the country's land + sea base map, simplifies them and writes wwf_site/data/sitesgeo.json:
one row per counted site with its SVG path (km, y flipped, same frame as geo.json) and its site_id.
Site details (name, designation, year, governance, net areas) come from data/sites.json via site_id.
"""
import json, os
import geopandas as gpd
from shapely.ops import unary_union
from shapely.validation import make_valid

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ROOT)
WS = os.environ.get("VARIANT") == "ws"   # second site: Morocco including Western Sahara
OUT = os.path.join(ROOT, "wwf_site_ws" if WS else "wwf_site", "data", "sitesgeo.json")
C = [("TUN", "tunisia", "PA_included_buffered_moll.gpkg", "pa_included"),
     ("DZA", "algeria", "PA_OECM_included_buffered_moll.gpkg", "included_sites"),
     ("MAR", "morocco_incl_western_sahara" if WS else "morocco", "PA_OECM_included_buffered_moll.gpkg", "included_sites"),
     ("LBY", "libya", "PA_OECM_included_buffered_moll.gpkg", "included_sites"),
     ("EGY", "egypt", "PA_OECM_included_buffered_moll.gpkg", "included_sites")]
TOL = {"TUN": 300, "DZA": 1200, "MAR": 500, "LBY": 800, "EGY": 900}


def polys(g):
    g = make_valid(g)
    if g.geom_type in ("Polygon", "MultiPolygon"):
        return g
    return unary_union([p for p in getattr(g, "geoms", []) if p.geom_type in ("Polygon", "MultiPolygon")])


def path(g, tol):
    g = g.simplify(tol, preserve_topology=True)
    out = []
    for pg in getattr(g, "geoms", [g]):
        if pg.geom_type != "Polygon":
            continue
        for ring in [pg.exterior, *pg.interiors]:
            cs = list(ring.coords)
            if len(cs) >= 4:
                out.append("M" + "L".join(f"{x/1000:.2f},{-y/1000:.2f}" for x, y in cs) + "Z")
    return "".join(out)


rows = []
for iso, folder, gpkg, layer in C:
    o = os.path.join(BASE, folder, "03_analysis", "outputs")
    sites = gpd.read_file(os.path.join(o, gpkg), layer=layer).to_crs("ESRI:54009")
    realms = gpd.read_file(os.path.join(o, f"base_map_realms_{iso}.shp")).to_crs("ESRI:54009")
    juris = polys(unary_union([polys(g) for g in realms[realms.realm.isin(["terrestrial", "marine_coastal"])].geometry]))
    n = 0
    for r in sites.itertuples():
        g = polys(polys(r.geometry).intersection(juris))
        if g.is_empty:
            continue
        d = path(g, TOL[iso])
        if not d:  # very small site: keep a minimal shape so it stays clickable when zoomed in
            d = path(g, TOL[iso] / 10)
        if not d:
            continue
        rows.append(dict(iso3=iso, site_id=str(int(r.site_id)), area_km2=round(g.area / 1e6, 3), d=d))
        n += 1
    print(iso, n, "sites")
json.dump(rows, open(OUT, "w"), separators=(",", ":"))
print("written", OUT, f"{os.path.getsize(OUT)/1024:.0f} KB")
