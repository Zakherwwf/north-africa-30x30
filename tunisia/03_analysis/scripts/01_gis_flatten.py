"""GBF Headline Indicator 3.1 – Tunisia GIS run (metadata steps 1-6).

Inputs  : ../../01_data (WDPA October 2026, geoBoundaries ADM0, Marine Regions EEZ v12,
          RESOLVE Ecoregions 2017, MEOW, HydroRIVERS v1.0)
Outputs : ../outputs (flattened layers, per-site net areas, overlap report, ecosystem and
          inland-water overlaps, results.json)

Run with: python 01_gis_flatten.py   (needs geopandas, shapely>=2, pyproj)
"""
import json, os
import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union
from shapely.validation import make_valid

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "../../01_data")
OUT = os.path.join(HERE, "../outputs")
os.makedirs(OUT, exist_ok=True)
MOLL = "ESRI:54009"
KM2 = 1e6


def fix(g):
    g = make_valid(g)
    if g.geom_type == "GeometryCollection":
        g = unary_union([p for p in g.geoms if p.area > 0])
    return g


# ------------------------------------------------------------------ base map
land = gpd.read_file(f"{DATA}/boundaries/geoBoundaries-TUN-ADM0.geojson").to_crs(MOLL)
eez = gpd.read_file(f"{DATA}/boundaries/MarineRegions_EEZ_v12_TUN.geojson").to_crs(MOLL)
LAND0 = fix(land.union_all())
EEZ = fix(eez.union_all())
# inland waters cut out of the land outline belong to the terrestrial & inland-waters realm: fill interior holes
from shapely.geometry import Polygon, MultiPolygon
LAND = fix(unary_union([Polygon(p.exterior) for p in (LAND0.geoms if isinstance(LAND0, MultiPolygon) else [LAND0])]))
# coastal lagoons / internal waters lying between the land outline and the EEZ inner edge would fall in
# neither realm: close the union by 5 km and keep only the gap pieces that touch the EEZ (coast, not land borders)
J0 = LAND.union(EEZ)
gap = J0.buffer(5000).buffer(-5000).difference(J0)
near_eez = EEZ.buffer(100)
COAST_GAP = unary_union([g for g in getattr(gap, "geoms", [gap]) if g.intersects(near_eez)])
SEA = fix(EEZ.union(COAST_GAP)).difference(LAND)      # marine & coastal realm = EEZ + coastal gaps, minus land
print(f"Land area {LAND.area/KM2:,.2f} km2 (holes filled: {(LAND.area-LAND0.area)/KM2:,.2f})   "
      f"Marine {SEA.area/KM2:,.2f} km2 (coastal gaps added: {COAST_GAP.area/KM2:,.2f})")
gpd.GeoDataFrame(dict(realm=["terrestrial", "marine_coastal", "coastal_gap_added"]),
                 geometry=[LAND, SEA, COAST_GAP], crs=MOLL).to_crs(4326).to_file(f"{OUT}/base_map_realms_TUN.shp")

# ------------------------------------------------------------------ step 1-3: load, filter, buffer
poly = gpd.read_file(f"{DATA}/wdpa/WDPA_TUN_polygons.geojson")
pts = gpd.read_file(f"{DATA}/wdpa/WDPA_TUN_points.geojson")
poly["geom_kind"], pts["geom_kind"] = "Polygon", "Point"
allsites = pd.concat([poly, pts], ignore_index=True)


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
# points -> circles of reported area (metadata step 3); Mollweide is equal-area
isp = inc.geom_kind == "Point"
inc.loc[isp, "geometry"] = inc.loc[isp].apply(
    lambda r: r.geometry.buffer((r["rep_area"] * KM2 / 3.141592653589793) ** 0.5, 64), axis=1)
inc["geometry"] = inc.geometry.apply(fix)
inc["moll_area"] = inc.geometry.area / KM2

# ------------------------------------------------------------------ step 5: intersect with base map
inc["g_terr"] = inc.geometry.apply(lambda g: g.intersection(LAND))
inc["g_mar"] = inc.geometry.apply(lambda g: g.intersection(SEA))
inc["clip_terr"] = inc.g_terr.apply(lambda g: g.area / KM2)
inc["clip_mar"] = inc.g_mar.apply(lambda g: g.area / KM2)

# ------------------------------------------------------------------ step 4: flatten (dissolve)
FLAT_T = unary_union(list(inc.g_terr))
FLAT_M = unary_union(list(inc.g_mar))
print(f"Gross terrestrial {inc.clip_terr.sum():,.2f}  flattened {FLAT_T.area/KM2:,.2f}")
print(f"Gross marine      {inc.clip_mar.sum():,.2f}  flattened {FLAT_M.area/KM2:,.2f}")

# overlap attribution: earliest designated first, unknown year (0) last, ties -> larger site first
inc["yr_key"] = inc.status_yr.apply(lambda y: y if y and y > 0 else 9999)
inc = inc.sort_values(["yr_key", "moll_area"], ascending=[True, False])
cov_t, cov_m = None, None
net_t, net_m = [], []
for _, r in inc.iterrows():
    nt = r.g_terr if cov_t is None else r.g_terr.difference(cov_t)
    nm = r.g_mar if cov_m is None else r.g_mar.difference(cov_m)
    net_t.append(nt.area / KM2); net_m.append(nm.area / KM2)
    cov_t = r.g_terr if cov_t is None else cov_t.union(r.g_terr)
    cov_m = r.g_mar if cov_m is None else cov_m.union(r.g_mar)
inc["net_terr"], inc["net_mar"] = net_t, net_m
print(f"Sum of net terrestrial {inc.net_terr.sum():,.3f}   net marine {inc.net_mar.sum():,.3f}")

# ------------------------------------------------------------------ overlap pairs report
pairs = []
rows = list(inc.itertuples())
sidx = gpd.GeoSeries([r.geometry for r in rows]).sindex
for i, a in enumerate(rows):
    for j in sidx.query(a.geometry, predicate="intersects"):
        if j <= i:
            continue
        b = rows[j]
        ov = a.geometry.intersection(b.geometry).area / KM2
        if ov > 0.01:
            pairs.append(dict(site_a=a.site_id, name_a=a.name_eng, desig_a=a.desig_eng, site_b=b.site_id,
                              name_b=b.name_eng, desig_b=b.desig_eng, overlap_km2=round(ov, 3)))
pd.DataFrame(pairs).sort_values("overlap_km2", ascending=False).to_csv(f"{OUT}/overlap_pairs.csv", index=False)
print(f"{len(pairs)} overlapping pairs")

# ------------------------------------------------------------------ outputs: per-site table and layers
cols = ["site_id", "site_pid", "name_eng", "name", "desig", "desig_eng", "desig_type", "iucn_cat", "realm",
        "rep_area", "rep_m_area", "gis_area", "gis_m_area", "status", "status_yr", "gov_type", "mang_auth",
        "geom_kind"]
tab = allsites[cols + ["excluded"]].merge(
    inc[["site_id", "moll_area", "clip_terr", "clip_mar", "net_terr", "net_mar"]], on="site_id", how="left")
tab.to_csv(f"{OUT}/sites_net_areas.csv", index=False)

inc_out = inc[cols + ["moll_area", "clip_terr", "clip_mar", "net_terr", "net_mar"]].copy()
inc_out = gpd.GeoDataFrame(inc_out, geometry=list(inc.geometry), crs=MOLL)
inc_out.to_file(f"{OUT}/PA_included_buffered_moll.gpkg", layer="pa_included")
flat = gpd.GeoDataFrame({"realm": ["terrestrial", "marine"], "area_km2": [FLAT_T.area / KM2, FLAT_M.area / KM2]},
                        geometry=[FLAT_T, FLAT_M], crs=MOLL)
flat.to_file(f"{OUT}/PA_flattened_TUN_moll.shp")
flat.to_crs(4326).to_file(f"{OUT}/PA_flattened_TUN_wgs84.geojson")

# ------------------------------------------------------------------ ecosystems: terrestrial ecoregions
eco = gpd.read_file(f"{DATA}/ecoregions/RESOLVE_Ecoregions2017_TUN_clip.shp").to_crs(MOLL)
eco_rows = []
for (eid, name, biome), g in eco.groupby(["ECO_ID", "ECO_NAME", "BIOME_NAME"]):
    geom = fix(g.union_all()).intersection(LAND)
    eco_rows.append(dict(eco_id=int(eid), eco_name=name, biome=biome, extent_km2=geom.area / KM2,
                         pa_km2=geom.intersection(FLAT_T).area / KM2))
pd.DataFrame(eco_rows).to_csv(f"{OUT}/ecoregion_coverage.csv", index=False)

# marine ecoregions (MEOW) within the marine realm
meow = gpd.read_file(f"{DATA}/marine_ecoregions/MEOW_bbox.geojson").to_crs(MOLL)
meow_rows = []
for _, r in meow.iterrows():
    geom = fix(r.geometry).intersection(SEA)
    if geom.area > 0:
        meow_rows.append(dict(eco_code=int(r.eco_code), ecoregion=r.ecoregion, province=r.get("province"),
                              extent_km2=geom.area / KM2, pa_km2=geom.intersection(FLAT_M).area / KM2))
meow_df = pd.DataFrame(meow_rows)
meow_df.to_csv(f"{OUT}/marine_ecoregion_coverage.csv", index=False)
gpd.GeoDataFrame(meow_rows, geometry=[fix(r.geometry).intersection(SEA) for _, r in meow.iterrows()
                                      if fix(r.geometry).intersection(SEA).area > 0], crs=MOLL) \
    .to_crs(4326).to_file(f"{DATA}/marine_ecoregions/MEOW_TUN_EEZ_clip.shp")

# ------------------------------------------------------------------ inland waters: rivers
riv = gpd.read_file(f"{DATA}/inland_waters/HydroRIVERS_v10_TUN_clip.shp").to_crs(MOLL)
riv_len = riv.geometry.length.sum() / 1000
riv_in = riv.geometry.intersection(FLAT_T).length.sum() / 1000
print(f"Rivers: {riv_len:,.1f} km total, {riv_in:,.1f} km inside PAs")

# ------------------------------------------------------------------ simplified geometry for the guide (km, Mollweide)
geo = {"land": json.loads(gpd.GeoSeries([LAND.simplify(800)]).to_json())["features"][0]["geometry"],
       "sea": json.loads(gpd.GeoSeries([SEA.simplify(800)]).to_json())["features"][0]["geometry"],
       "flat_t": json.loads(gpd.GeoSeries([FLAT_T.simplify(250)]).to_json())["features"][0]["geometry"],
       "flat_m": json.loads(gpd.GeoSeries([FLAT_M.simplify(250)]).to_json())["features"][0]["geometry"],
       "sites": [dict(id=int(r.site_id), name=r.name_eng, desig=r.desig_eng, dtype=r.desig_type,
                      geom=json.loads(gpd.GeoSeries([r.geometry.simplify(250)]).to_json())["features"][0]["geometry"])
                 for r in inc.itertuples()]}
json.dump(geo, open(f"{OUT}/geom_moll_simplified.json", "w"))

res = dict(land_km2=LAND.area / KM2, marine_km2=SEA.area / KM2,
           gross_terr=inc.clip_terr.sum(), gross_mar=inc.clip_mar.sum(),
           flat_terr=FLAT_T.area / KM2, flat_mar=FLAT_M.area / KM2,
           n_records=len(allsites), n_included=len(inc), excluded=allsites.excluded.value_counts().to_dict(),
           rivers_km=riv_len, rivers_in_pa_km=riv_in, overlap_pairs=len(pairs))
json.dump(res, open(f"{OUT}/results.json", "w"), indent=1)
print(json.dumps(res, indent=1))
