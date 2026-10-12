"""KBA disaggregation for Indicator 3.1 – Tunisia, using the official KBA polygons (World Database of KBAs, September 2026).

For each Tunisian KBA: area, land / ocean fractions, mountain overlap (GMBA Inventory v2.0 standard),
freshwater flag, and the area covered by the flattened PA layer from 01_gis_flatten.py.
Run after 01_gis_flatten.py.
"""
import json, os
import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union
from shapely.validation import make_valid

HERE = os.path.dirname(os.path.abspath(__file__))
DATA, OUT = f"{HERE}/../../01_data", f"{HERE}/../outputs"
MOLL, KM2 = "ESRI:54009", 1e6
THRESH = 0.05          # metadata: >=5% ocean overlap -> marine KBA; same share used for land and mountain


def fix(g):
    g = make_valid(g)
    if g.geom_type == "GeometryCollection":
        g = unary_union([p for p in g.geoms if p.area > 0])
    return g


realms = gpd.read_file(f"{OUT}/base_map_realms_TUN.shp").to_crs(MOLL).set_index("realm")
land = fix(realms.loc["terrestrial", "geometry"])          # same base map as the headline (01_gis_flatten.py)
sea = fix(realms.loc["marine_coastal", "geometry"])
juris = fix(land.union(sea))
flat = gpd.read_file(f"{OUT}/PA_flattened_TUN_moll.shp").to_crs(MOLL)
PA = fix(flat.union_all())

kba = gpd.read_file(f"{DATA}/kba/KBAsGlobal_2026_September_TUN_polygons.shp").to_crs(MOLL)
kba["geometry"] = kba.geometry.apply(fix)

# mountains: GMBA Inventory v2.0 (standard, basic) clipped to Tunisia
gm_path = f"{DATA}/mountains/GMBA_Inventory_v2.0_TUN_clip.shp"
if not os.path.exists(gm_path):
    gm = gpd.read_file(f"/vsizip/{DATA}/mountains/_global_download/GMBA_Inventory_v2.0_standard_basic.zip/GMBA_Inventory_v2.0_standard_basic.shp",
                       bbox=(7, 30, 12, 38))
    gm = gpd.clip(gm.to_crs(MOLL), land)
    gm.to_crs(4326).to_file(gm_path)
MOUNT = fix(gpd.read_file(gm_path).to_crs(MOLL).union_all())

# freshwater: factsheet 'System' field, site-name keywords, or freshwater trigger taxa
facts = pd.read_csv(f"{DATA}/kba/KBA_Tunisia_sites.csv").set_index("SitRecID")
trig = pd.read_csv(f"{DATA}/kba/KBA_TUN_trigger_species_September2026.csv")
FW_CLASSES = {"ACTINOPTERYGII", "AMPHIBIA"}
FW_ORDERS = {"ODONATA", "UNIONIDA"}
fw_trig = set(trig[trig["Class"].isin(FW_CLASSES) | trig["Order"].isin(FW_ORDERS)].SitRecID)
FW_WORDS = ("barrage", "garaet", "garâa", "oued", "lac ", "river", "aïn", "ain ", "tourbi", "aqueduc", "douza")

rows, gaps = [], []
for r in kba.itertuples():
    g = r.geometry
    a = g.area / KM2
    in_j = g.intersection(juris)
    a_land = g.intersection(land).area / KM2
    a_mount = g.intersection(MOUNT).area / KM2
    cov = in_j.intersection(PA)
    name = r.IntName
    sysf = str(facts.loc[r.SitRecID, "system"]) if r.SitRecID in facts.index else ""
    fresh = "freshwater" in sysf or any(w in name.lower() for w in FW_WORDS) or r.SitRecID in fw_trig
    rows.append(dict(SitRecID=int(r.SitRecID), name=name, kba_class=r.KbaClass, last_update=r.LastUpdate,
                     area_km2=a, area_in_jurisdiction_km2=in_j.area / KM2, land_frac=a_land / a, ocean_frac=1 - a_land / a,
                     mountain_frac=a_mount / a, terrestrial="Y" if a_land / a >= THRESH else "N",
                     freshwater="Y" if fresh else "N", mountain="Y" if a_mount / a >= THRESH else "N",
                     marine="Y" if 1 - a_land / a >= THRESH else "N",
                     pa_covered_km2=cov.area / KM2, pa_cov_pct=cov.area / KM2 / a * 100,
                     kba_db_pa_cov_pct=facts.loc[r.SitRecID, "pa_coverage_pct"] if r.SitRecID in facts.index else None))
    gaps.append(in_j.difference(PA))

df = pd.DataFrame(rows).sort_values("pa_cov_pct")
df.to_csv(f"{OUT}/kba_coverage_TUN.csv", index=False)
out = kba[["SitRecID", "IntName", "KbaClass", "geometry"]].merge(df.drop(columns="name"), on="SitRecID")
out.to_crs(4326).to_file(f"{OUT}/KBA_coverage_TUN.shp")
gap = gpd.GeoDataFrame(dict(SitRecID=kba.SitRecID, name=kba.IntName,
                            unprot_km2=[g.area / KM2 for g in gaps]), geometry=gaps, crs=MOLL)
gap = gap[gap.unprot_km2 > 0.001]
gap.to_crs(4326).to_file(f"{OUT}/KBA_unprotected_parts_TUN.shp")

# foreign KBAs reaching into Tunisian land or EEZ (reported, not counted in the national KBA mean)
allk = gpd.read_file("/Users/zakherfrogman/Documents/Tool for 30x30/KBAs/KBA_Data/KBAsGlobal_2026_September_02_POL.shp",
                     bbox=(7, 30, 16, 38.5)) if os.path.exists("/Users/zakherfrogman/Documents/Tool for 30x30/KBAs/KBA_Data") else None
foreign = []
if allk is not None:
    allk = allk[allk.ISO3 != "TUN"].to_crs(MOLL)
    for r in allk.itertuples():
        ov = fix(r.geometry).intersection(juris).area / KM2
        if ov > 0.001:
            foreign.append(dict(SitRecID=int(r.SitRecID), ISO3=r.ISO3, name=r.IntName, overlap_with_TUN_km2=round(ov, 3)))
    pd.DataFrame(foreign).to_csv(f"{OUT}/kba_foreign_overlapping_TUN.csv", index=False)

# simplified geometry for the guide
json.dump({"kba": [dict(id=int(r.SitRecID), name=r.IntName, pct=float(df.set_index("SitRecID").loc[r.SitRecID, "pa_cov_pct"]),
                        geom=json.loads(gpd.GeoSeries([r.geometry.simplify(400)]).to_json())["features"][0]["geometry"])
                   for r in kba.itertuples()]}, open(f"{OUT}/kba_geom_moll_simplified.json", "w"))

s = dict(n=len(df), mean_all=df.pa_cov_pct.mean(), complete=int((df.pa_cov_pct >= 98).sum()),
         partial=int(((df.pa_cov_pct > 0) & (df.pa_cov_pct < 98)).sum()), none=int((df.pa_cov_pct == 0).sum()),
         n_terr=int((df.terrestrial == "Y").sum()), n_marine=int((df.marine == "Y").sum()),
         n_fresh=int((df.freshwater == "Y").sum()), n_mount=int((df.mountain == "Y").sum()),
         total_kba_km2=df.area_km2.sum(), total_covered_km2=df.pa_covered_km2.sum(), foreign=foreign)
for grp in ("terrestrial", "marine", "freshwater", "mountain"):
    s[f"mean_{grp}"] = df[df[grp] == "Y"].pa_cov_pct.mean()
json.dump(s, open(f"{OUT}/kba_results.json", "w"), indent=1)
print(json.dumps(s, indent=1))
print(df[["SitRecID", "name", "area_km2", "ocean_frac", "mountain_frac", "freshwater", "pa_cov_pct", "kba_db_pa_cov_pct"]]
      .round(2).to_string())
