"""GBF Headline Indicator 3.1 – country GIS run (metadata steps 1-6), PAs and OECMs.

Country set in country.json. Inputs in ../../01_data; outputs in ../outputs.
- Base map: land (geoBoundaries ADM0, interior holes filled) and sea (Marine Regions EEZ v12 + coastal gaps, minus land).
- Filter: drop STATUS Proposed / Not Reported, UNESCO-MAB Biosphere Reserves, points without REP_AREA.
- Buffer points to circles of REP_AREA; clip to land / sea; Mollweide.
- Flatten PAs; OECMs: erase all PA area, then flatten (metadata OECM step 4).
- Net area per site: PAs first, then OECMs; within each, earliest designation first, ties to the larger site.
"""
import json, os
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely.validation import make_valid

HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(f"{HERE}/country.json"))
ISO = C["iso3"]
DATA, OUT = f"{HERE}/../../01_data", f"{HERE}/../outputs"
os.makedirs(OUT, exist_ok=True)
MOLL, KM2 = "ESRI:54009", 1e6


def fix(g):
    g = make_valid(g)
    if g.geom_type == "GeometryCollection":
        g = unary_union([p for p in g.geoms if p.area > 0])
    return g


def polys(g):
    """Valid, polygon-only version of a geometry (drops line/point slivers produced by overlays)."""
    g = make_valid(g)
    if g.geom_type in ("Polygon", "MultiPolygon"):
        return g
    return unary_union([p for p in getattr(g, "geoms", []) if p.geom_type in ("Polygon", "MultiPolygon")]) or Polygon()


def gj(g, tol):
    return json.loads(gpd.GeoSeries([g.simplify(tol)]).to_json())["features"][0]["geometry"]


# ------------------------------------------------------------------ base map
land = gpd.read_file(f"{DATA}/boundaries/geoBoundaries-{ISO}-ADM0.geojson").to_crs(MOLL)
eez = gpd.read_file(f"{DATA}/boundaries/MarineRegions_EEZ_v12_{ISO}.geojson").to_crs(MOLL)
land["geometry"] = land.geometry.apply(make_valid)   # some source boundaries (e.g. EEZ v12 for Egypt) are invalid
eez["geometry"] = eez.geometry.apply(make_valid)
LAND0, EEZ = polys(land.union_all()), polys(eez.union_all())
LAND = fix(unary_union([Polygon(p.exterior) for p in (LAND0.geoms if isinstance(LAND0, MultiPolygon) else [LAND0])]))
J0 = LAND.union(EEZ)
gap = J0.buffer(5000).buffer(-5000).difference(J0)
COAST_GAP = unary_union([g for g in getattr(gap, "geoms", [gap]) if g.intersects(EEZ.buffer(100))])
SEA = fix(EEZ.union(COAST_GAP)).difference(LAND)
print(f"Land {LAND.area/KM2:,.2f} km2 (holes filled {(LAND.area-LAND0.area)/KM2:,.2f}); "
      f"sea {SEA.area/KM2:,.2f} km2 (coastal gaps {COAST_GAP.area/KM2:,.2f})")
gpd.GeoDataFrame(dict(realm=["terrestrial", "marine_coastal", "coastal_gap_added"]), geometry=[LAND, SEA, COAST_GAP], crs=MOLL) \
    .to_crs(4326).to_file(f"{OUT}/base_map_realms_{ISO}.shp")

# ------------------------------------------------------------------ steps 1-3: load, filter, buffer
parts = []
for f, kind, typ in ((f"WDPA_{ISO}_polygons", "Polygon", "PA"), (f"WDPA_{ISO}_points", "Point", "PA"),
                     (f"WDOECM_{ISO}_polygons", "Polygon", "OECM"), (f"WDOECM_{ISO}_points", "Point", "OECM")):
    p = f"{DATA}/wdpa/{f}.geojson"
    if os.path.exists(p):
        g = gpd.read_file(p)
        if len(g):
            g["geom_kind"], g["ptype"] = kind, typ
            parts.append(g)
allsites = pd.concat(parts, ignore_index=True)
for c in ("gis_area", "gis_m_area"):
    if c not in allsites:
        allsites[c] = None


def exclusion(r):
    if r["status"] in ("Proposed", "Not Reported"):
        return f"STATUS = {r['status']}"
    if r["desig_eng"] == "UNESCO-MAB Biosphere Reserve":
        return "UNESCO-MAB Biosphere Reserve"
    if r["geom_kind"] == "Point" and not (r["rep_area"] or 0) > 0:
        return "Point without REP_AREA"
    return ""


allsites["excluded"] = allsites.apply(exclusion, axis=1)
allsites = allsites.to_crs(MOLL)
inc = allsites[allsites.excluded == ""].copy()
isp = inc.geom_kind == "Point"
inc.loc[isp, "geometry"] = inc.loc[isp].apply(lambda r: r.geometry.buffer((r["rep_area"] * KM2 / 3.141592653589793) ** 0.5, 64), axis=1)
inc["geometry"] = inc.geometry.apply(fix)
inc["moll_area"] = inc.geometry.area / KM2
inc["g_terr"] = inc.geometry.apply(lambda g: polys(g.intersection(LAND)))
inc["g_mar"] = inc.geometry.apply(lambda g: polys(g.intersection(SEA)))
inc["clip_terr"] = inc.g_terr.apply(lambda g: g.area / KM2)
inc["clip_mar"] = inc.g_mar.apply(lambda g: g.area / KM2)

# ------------------------------------------------------------------ step 4: flatten PAs; OECMs erase PAs then flatten
pa, oe = inc[inc.ptype == "PA"], inc[inc.ptype == "OECM"]
PA_T, PA_M = polys(unary_union(list(pa.g_terr))), polys(unary_union(list(pa.g_mar)))
OE_T = polys(unary_union(list(oe.g_terr)).difference(PA_T)) if len(oe) else Polygon()
OE_M = polys(unary_union(list(oe.g_mar)).difference(PA_M)) if len(oe) else Polygon()
R = dict(land_km2=LAND.area / KM2, marine_km2=SEA.area / KM2,
         gross_pa_terr=pa.clip_terr.sum(), gross_pa_mar=pa.clip_mar.sum(), gross_oecm_terr=oe.clip_terr.sum(), gross_oecm_mar=oe.clip_mar.sum(),
         flat_pa_terr=PA_T.area / KM2, flat_pa_mar=PA_M.area / KM2, flat_oecm_terr=OE_T.area / KM2, flat_oecm_mar=OE_M.area / KM2)
print(json.dumps({k: round(v, 2) for k, v in R.items()}, indent=1))

# net per-site areas: PAs before OECMs, earliest year first (unknown last), ties -> larger
inc["is_oecm"] = (inc.ptype == "OECM").astype(int)
inc["yr_key"] = inc.status_yr.apply(lambda y: y if y and y > 0 else 9999)
inc = inc.sort_values(["is_oecm", "yr_key", "moll_area"], ascending=[True, True, False])
cov_t = cov_m = None
nt_l, nm_l = [], []
for _, r in inc.iterrows():
    nt = r.g_terr if cov_t is None else r.g_terr.difference(cov_t)
    nm = r.g_mar if cov_m is None else r.g_mar.difference(cov_m)
    nt_l.append(nt.area / KM2); nm_l.append(nm.area / KM2)
    cov_t = r.g_terr if cov_t is None else polys(cov_t.union(r.g_terr))
    cov_m = r.g_mar if cov_m is None else polys(cov_m.union(r.g_mar))
inc["net_terr"], inc["net_mar"] = nt_l, nm_l
for t in ("PA", "OECM"):
    s = inc[inc.ptype == t]
    print(f"{t}: sum net terr {s.net_terr.sum():,.3f}  sum net marine {s.net_mar.sum():,.3f}")

# overlap pairs
pairs, rows = [], list(inc.itertuples())
sidx = gpd.GeoSeries([r.geometry for r in rows]).sindex
for i, a in enumerate(rows):
    for j in sidx.query(a.geometry, predicate="intersects"):
        if j <= i:
            continue
        b = rows[j]
        ov = a.geometry.intersection(b.geometry).area / KM2
        if ov > 0.01:
            pairs.append(dict(site_a=a.site_id, type_a=a.ptype, name_a=a.name_eng, desig_a=a.desig_eng,
                              site_b=b.site_id, type_b=b.ptype, name_b=b.name_eng, desig_b=b.desig_eng, overlap_km2=round(ov, 3)))
PAIR_COLS = ["site_a", "type_a", "name_a", "desig_a", "site_b", "type_b", "name_b", "desig_b", "overlap_km2"]
pd.DataFrame(pairs, columns=PAIR_COLS).sort_values("overlap_km2", ascending=False).to_csv(f"{OUT}/overlap_pairs.csv", index=False)
R["overlap_pairs"] = len(pairs)

# ------------------------------------------------------------------ outputs: per-site table and layers
cols = ["site_id", "site_pid", "ptype", "name_eng", "name", "desig", "desig_eng", "desig_type", "iucn_cat", "realm", "rep_area",
        "rep_m_area", "gis_area", "gis_m_area", "status", "status_yr", "gov_type", "mang_auth", "geom_kind"]
cols = [c for c in cols if c in allsites.columns]
tab = allsites[cols + ["excluded"]].merge(inc[["site_id", "moll_area", "clip_terr", "clip_mar", "net_terr", "net_mar"]], on="site_id", how="left")
tab.to_csv(f"{OUT}/sites_net_areas.csv", index=False)
gpd.GeoDataFrame(inc[cols + ["moll_area", "clip_terr", "clip_mar", "net_terr", "net_mar"]], geometry=list(inc.geometry), crs=MOLL) \
    .to_file(f"{OUT}/PA_OECM_included_buffered_moll.gpkg", layer="included_sites")
flat = gpd.GeoDataFrame({"layer": ["PA", "PA", "OECM_PA_erased", "OECM_PA_erased"], "realm": ["terrestrial", "marine"] * 2,
                         "area_km2": [PA_T.area / KM2, PA_M.area / KM2, OE_T.area / KM2, OE_M.area / KM2]},
                        geometry=[PA_T, PA_M, OE_T, OE_M], crs=MOLL)
flat = flat[~flat.geometry.is_empty]   # e.g. no OECMs, or no marine PAs
flat.to_file(f"{OUT}/PA_OECM_flattened_{ISO}_moll.shp")
flat.to_crs(4326).to_file(f"{OUT}/PA_OECM_flattened_{ISO}_wgs84.geojson")


# ------------------------------------------------------------------ ecosystems, rivers
def cover(geom, a, b):
    return geom.intersection(a).area / KM2, geom.intersection(b).area / KM2


eco = gpd.read_file(f"{DATA}/ecoregions/RESOLVE_Ecoregions2017_{ISO}_clip.shp").to_crs(MOLL)
er = []
for (eid, name, biome), g in eco.groupby(["ECO_ID", "ECO_NAME", "BIOME_NAME"]):
    geom = polys(polys(g.union_all()).intersection(LAND))
    p, o = cover(geom, PA_T, OE_T)
    er.append(dict(eco_id=int(eid), eco_name=name, biome=biome, extent_km2=geom.area / KM2, pa_km2=p, oecm_km2=o))
pd.DataFrame(er).to_csv(f"{OUT}/ecoregion_coverage.csv", index=False)

meow = gpd.read_file(f"{DATA}/marine_ecoregions/MEOW_bbox.geojson").to_crs(MOLL)
mr, mg = [], []
for _, r in meow.iterrows():
    geom = polys(polys(r.geometry).intersection(SEA))
    if geom.area > 0:
        p, o = cover(geom, PA_M, OE_M)
        mr.append(dict(eco_code=int(r.eco_code), ecoregion=r.ecoregion, extent_km2=geom.area / KM2, pa_km2=p, oecm_km2=o)); mg.append(geom)
pd.DataFrame(mr).to_csv(f"{OUT}/marine_ecoregion_coverage.csv", index=False)
gpd.GeoDataFrame(mr, geometry=mg, crs=MOLL).to_crs(4326).to_file(f"{DATA}/marine_ecoregions/MEOW_{ISO}_EEZ_clip.shp")

riv = gpd.read_file(f"{DATA}/inland_waters/HydroRIVERS_v10_{ISO}_clip.shp").to_crs(MOLL)
R["rivers_km"] = riv.geometry.length.sum() / 1000
R["rivers_in_pa_km"] = riv.geometry.intersection(PA_T).length.sum() / 1000
R["rivers_in_oecm_km"] = riv.geometry.intersection(OE_T).length.sum() / 1000

# ------------------------------------------------------------------ geometry for the guide
json.dump({"land": gj(LAND, 2000), "sea": gj(SEA, 2000), "pa_t": gj(PA_T, 800), "pa_m": gj(PA_M, 300),
           "oe_t": gj(OE_T, 1500) if not OE_T.is_empty else {"type": "GeometryCollection", "geometries": []},
           "oe_m": gj(OE_M, 800) if not OE_M.is_empty else {"type": "GeometryCollection", "geometries": []},
           "sites": [dict(id=int(r.site_id), name=r.name_eng, desig=r.desig_eng, dtype=r.desig_type, ptype=r.ptype,
                          geom=gj(r.geometry, 800)) for r in inc.itertuples()]},
          open(f"{OUT}/geom_moll_simplified.json", "w"))
R.update(n_records=len(allsites), n_included=len(inc), n_pa_included=int((inc.ptype == "PA").sum()),
         n_oecm_included=int((inc.ptype == "OECM").sum()), excluded=allsites.excluded.value_counts().to_dict())
json.dump(R, open(f"{OUT}/results.json", "w"), indent=1)
print(json.dumps(R, indent=1))
