"""KBA disaggregation for Indicator 3.1 using the official KBA polygons (World Database of KBAs, September 2026).

For each KBA of the country in country.json: area, land / ocean fractions, mountain overlap (GMBA v2.0),
freshwater flag, and the area covered by the flattened PA layer and by the PA-erased OECM layer.
KBA points without an area are listed but cannot be measured. Run after 01_gis_flatten.py.
"""
import json, os
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.validation import make_valid

HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(f"{HERE}/country.json"))
ISO = C["iso3"]
DATA, OUT = f"{HERE}/../../01_data", f"{HERE}/../outputs"
MOLL, KM2 = "ESRI:54009", 1e6
THRESH = 0.05          # metadata: >=5% ocean overlap -> marine KBA; same share used for land and mountain


def fix(g):
    g = make_valid(g)
    if g.geom_type == "GeometryCollection":
        g = unary_union([p for p in g.geoms if p.area > 0])
    return g


def polys(g):
    """Keep only the polygonal parts of a geometry (drops slivers reduced to lines/points)."""
    if g.geom_type in ("Polygon", "MultiPolygon"):
        return g
    return unary_union([p for p in getattr(g, "geoms", []) if p.geom_type in ("Polygon", "MultiPolygon")])


realms = gpd.read_file(f"{OUT}/base_map_realms_{ISO}.shp").to_crs(MOLL).set_index("realm")
land, sea = fix(realms.loc["terrestrial", "geometry"]), fix(realms.loc["marine_coastal", "geometry"])
juris = fix(land.union(sea))
fl = gpd.read_file(f"{OUT}/PA_OECM_flattened_{ISO}_moll.shp").to_crs(MOLL)
PA = fix(fl[fl.layer == "PA"].union_all())
OE = fix(fl[fl.layer == "OECM_PA_erased"].union_all()) if (fl.layer == "OECM_PA_erased").any() else Polygon()
MOUNT = fix(gpd.read_file(f"{DATA}/mountains/GMBA_Inventory_v2.0_{ISO}_clip.shp").to_crs(MOLL).union_all())

kba = gpd.read_file(f"{DATA}/kba/KBAsGlobal_2026_September_{ISO}_polygons.shp").to_crs(MOLL)
kba["kba_geom"] = "Polygon"
pts_path = f"{DATA}/kba/KBAsGlobal_2026_September_{ISO}_points.shp"
if os.path.exists(pts_path):     # KBA points with a reported area become circles of that area, as for WDPA points
    kp = gpd.read_file(pts_path).to_crs(MOLL)
    kp = kp[kp.RepAreaKM2 > 0].copy()
    if len(kp):
        kp["geometry"] = kp.apply(lambda r: r.geometry.buffer((r.RepAreaKM2 * KM2 / 3.141592653589793) ** 0.5, 64), axis=1)
        kp["kba_geom"] = "Point (buffered)"
        kba = gpd.GeoDataFrame(pd.concat([kba, kp.drop(columns=["RepAreaKM2"])], ignore_index=True), crs=MOLL)
kba["geometry"] = kba.geometry.apply(fix)
facts = pd.read_csv(f"{DATA}/kba/KBA_{C['name']}_sites.csv").set_index("SitRecID")
trig = pd.read_csv(f"{DATA}/kba/KBA_{ISO}_trigger_species_September2026.csv")
fw_trig = set(trig[trig["Class"].isin({"ACTINOPTERYGII", "AMPHIBIA"}) | trig["Order"].isin({"ODONATA", "UNIONIDA"})].SitRecID)
FW_WORDS = ("barrage", "garaet", "garâa", "oued", "lac ", "river", "aïn", "ain ", "tourbi", "aqueduc", "gueltat", "marais", "dayet", "oasis")

rows, gaps = [], []
for r in kba.itertuples():
    g = r.geometry
    a = g.area / KM2
    in_j = g.intersection(juris)
    a_land = g.intersection(land).area / KM2
    a_mount = g.intersection(MOUNT).area / KM2
    p = in_j.intersection(PA).area / KM2
    o = in_j.intersection(OE).area / KM2
    sysf = str(facts.loc[r.SitRecID, "system"]) if r.SitRecID in facts.index else ""
    fresh = "freshwater" in sysf or any(w in r.IntName.lower() for w in FW_WORDS) or r.SitRecID in fw_trig
    rows.append(dict(SitRecID=int(r.SitRecID), name=r.IntName, geom_type=r.kba_geom, kba_class=r.KbaClass, last_update=r.LastUpdate,
                     area_km2=a, land_frac=a_land / a, ocean_frac=max(0.0, 1 - a_land / a), mountain_frac=a_mount / a,
                     terrestrial="Y" if a_land / a >= THRESH else "N", freshwater="Y" if fresh else "N",
                     mountain="Y" if a_mount / a >= THRESH else "N", marine="Y" if 1 - a_land / a >= THRESH else "N",
                     pa_covered_km2=p, oecm_covered_km2=o, pa_cov_pct=p / a * 100, pa_oecm_cov_pct=(p + o) / a * 100,
                     kba_db_pa_cov_pct=facts.loc[r.SitRecID, "pa_coverage_pct"] if r.SitRecID in facts.index else None))
    gaps.append(polys(in_j.difference(PA).difference(OE)))

df = pd.DataFrame(rows).sort_values("pa_oecm_cov_pct")
df.to_csv(f"{OUT}/kba_coverage_{ISO}.csv", index=False)
kba[["SitRecID", "IntName", "KbaClass", "geometry"]].merge(df.drop(columns="name"), on="SitRecID").to_crs(4326) \
    .to_file(f"{OUT}/KBA_coverage_{ISO}.shp")
gap = gpd.GeoDataFrame(dict(SitRecID=kba.SitRecID, name=kba.IntName, unprot_km2=[g.area / KM2 for g in gaps]), geometry=gaps, crs=MOLL)
gap[gap.unprot_km2 > 0.001].to_crs(4326).to_file(f"{OUT}/KBA_unprotected_parts_{ISO}.shp")

pts = f"{DATA}/kba/KBAsGlobal_2026_September_{ISO}_points.shp"
kba_points = [r for r in gpd.read_file(pts)[["SitRecID", "IntName", "RepAreaKM2"]].to_dict("records") if not r["RepAreaKM2"] > 0] if os.path.exists(pts) else []

allk = gpd.read_file(os.path.normpath(os.path.join(HERE, C["global_sources"]["kba_global_polygons"])),
                     bbox=tuple(gpd.GeoSeries([juris], crs=MOLL).to_crs(4326).total_bounds))
foreign = []
for r in allk[allk.ISO3 != ISO].to_crs(MOLL).itertuples():
    ov = fix(r.geometry).intersection(juris).area / KM2
    if ov > 0.001:
        foreign.append(dict(SitRecID=int(r.SitRecID), ISO3=r.ISO3, name=r.IntName, overlap_km2=round(ov, 3)))
pd.DataFrame(foreign).to_csv(f"{OUT}/kba_foreign_overlapping_{ISO}.csv", index=False)

d = df.set_index("SitRecID")
json.dump({"kba": [dict(id=int(r.SitRecID), name=r.IntName, pct=float(d.loc[r.SitRecID, "pa_oecm_cov_pct"]),
                        geom=json.loads(gpd.GeoSeries([r.geometry.simplify(1500)]).to_json())["features"][0]["geometry"])
                   for r in kba.itertuples()]}, open(f"{OUT}/kba_geom_moll_simplified.json", "w"))


def summary(col):
    return dict(mean=df[col].mean(), complete=int((df[col] >= 98).sum()), partial=int(((df[col] > 0) & (df[col] < 98)).sum()),
                none=int((df[col] == 0).sum()))


s = dict(n=len(df), n_points_unmeasured=len(kba_points), points=kba_points, pa_only=summary("pa_cov_pct"), pa_oecm=summary("pa_oecm_cov_pct"),
         total_kba_km2=df.area_km2.sum(), foreign=foreign)
for grp in ("terrestrial", "marine", "freshwater", "mountain"):
    sub = df[df[grp] == "Y"]
    s[grp] = dict(n=len(sub), mean_pa=sub.pa_cov_pct.mean(), mean_pa_oecm=sub.pa_oecm_cov_pct.mean())
json.dump(s, open(f"{OUT}/kba_results.json", "w"), indent=1, default=str)
print(json.dumps(s, indent=1, default=str))
print(df[["SitRecID", "name", "area_km2", "ocean_frac", "mountain_frac", "freshwater", "pa_cov_pct", "pa_oecm_cov_pct", "kba_db_pa_cov_pct"]]
      .round(2).to_string())
