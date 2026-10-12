"""Assemble the configuration for the Indicator 3.1 Excel tool from the GIS outputs (country in country.json)."""
import json, os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(f"{HERE}/country.json"))
ISO, NAME = C["iso3"], C["name"]
DATA, OUT = f"{HERE}/../../01_data", f"{HERE}/../outputs"
t = pd.read_csv(f"{OUT}/sites_net_areas.csv")
pame = json.load(open(f"{DATA}/protected_planet/ProtectedPlanet_{ISO}_PAME_by_site.json"))
res = json.load(open(f"{OUT}/results.json"))
wl = json.load(open(f"{OUT}/glwd_results.json"))      # 03_wetlands_glwd.py

TOOLS = {"Management Effectiveness Tracking Tool (METT)": "METT"}
# evaluations recorded on one record are applied to the record holding the area for the same physical site
TRANSFER = {int(k): int(v) for k, v in C.get("pame_transfer", {}).items()}
evals = {}
for sid, d in pame.items():
    sid = int(sid)
    for tool, yrs in list(d.values())[0].items():
        for y in yrs:
            evals.setdefault(TRANSFER.get(sid, sid), []).append((tool, y, sid))

realm_code = {"Terrestrial": 0, "Coastal": 1, "Marine": 2}
t["yr_key"] = t.status_yr.apply(lambda y: y if y and y > 0 else 9999)
t["order"] = t.desig_type.map({"National": 0, "Regional": 1, "International": 2}).fillna(3)
t["is_oecm"] = (t.ptype == "OECM").astype(int)
t = t.sort_values(["is_oecm", "yr_key", "order", "site_id"])
reg = []
for r in t.itertuples():
    ev = evals.get(r.site_id)
    note, pm = [], ["N", "", "", "", ""]
    if ev:
        tool, yr, src = max(ev, key=lambda e: e[1])
        pm = ["Y", TOOLS.get(tool, "Other"), int(yr), "", ""]
        note.append("GD-PAME: " + "; ".join(f"{e[0]} {e[1]}" + (f" (from record {e[2]})" if e[2] != r.site_id else "")
                                           for e in sorted(ev, key=lambda e: -e[1])))
    excl = isinstance(r.excluded, str) and r.excluded
    if excl:
        note.append("Excluded in GIS: " + r.excluded)
    elif r.clip_terr + r.clip_mar > 0 and (r.net_terr + r.net_mar) < 0.9 * (r.clip_terr + r.clip_mar):
        note.append("PA area erased from OECM" if r.ptype == "OECM" else "Overlap attributed to earlier site")
    reg.append([int(r.site_id), r.name_eng, r.desig_eng, r.desig_type, r.ptype, r.iucn_cat, r.gov_type, r.status,
                int(r.status_yr) if r.status_yr and r.status_yr > 0 else "", realm_code.get(r.realm, 0), r.geom_kind,
                float(r.rep_area), float(r.rep_m_area),
                round(float(r.gis_area), 3) if r.gis_area == r.gis_area else "",
                round(float(r.gis_m_area), 3) if r.gis_m_area == r.gis_m_area else "",
                "Y" if r.desig_eng == "UNESCO-MAB Biosphere Reserve" else "N", "",
                "" if excl else round(r.net_terr, 3), "" if excl else round(r.net_mar, 3), *pm, "; ".join(note)])

# KBAs – official polygons, overlaid in 02_kba_overlay.py
kc = pd.read_csv(f"{OUT}/kba_coverage_{ISO}.csv").sort_values("SitRecID")
kba = [[int(r.SitRecID), r.name, round(r.area_km2, 3), round(r.ocean_frac, 3), r.terrestrial, r.freshwater, r.mountain,
        round(r.pa_covered_km2, 3), round(r.oecm_covered_km2, 3)] for r in kc.itertuples()]

# ecosystems
GET = C["biome_crosswalk"]
eco = pd.read_csv(f"{OUT}/ecoregion_coverage.csv")
eco["get"] = eco.biome.map(GET)
assert eco["get"].notna().all(), f"biome without GET crosswalk: {set(eco[eco["get"].isna()].biome)}"
biomes = {g: [round(d.extent_km2.sum(), 2), round(d.pa_km2.sum(), 2), round(d.oecm_km2.sum(), 2)] for g, d in eco.groupby("get")}
units = [["Terrestrial ecoregion (Dinerstein et al. 2017)", f"ECO-{r.eco_id}", r.eco_name, r.get, "Y",
          round(r.extent_km2, 2), round(r.pa_km2, 2), round(r.oecm_km2, 2)] for r in eco.itertuples()]
meow = pd.read_csv(f"{OUT}/marine_ecoregion_coverage.csv")
units += [["Marine ecoregion (Spalding et al. 2007)", f"MEOW-{r.eco_code}", r.ecoregion, "", "Y",
           round(r.extent_km2, 2), round(r.pa_km2, 2), round(r.oecm_km2, 2)] for r in meow.itertuples()]

n_poly = int(((t.geom_kind == "Polygon") & (t.ptype == "PA")).sum()); n_pt = int(((t.geom_kind == "Point") & (t.ptype == "PA")).sum())
n_oe = int((t.ptype == "OECM").sum())
cfg = {"out": os.path.abspath(f"{HERE}/../../04_tool/GBF_3.1_Tool_{NAME}_Worked_Example.xlsx"),
       "setup": {"4": NAME, "5": ISO, "6": C["reporting_year"], "7": C["wdpa_release"],
                 "8": f"World Database of KBAs, September 2026 release (KBAsGlobal_2026_September, {len(kba)} {NAME} polygons)",
                 "9": "geoBoundaries ADM0, inland holes filled (land) + Marine Regions EEZ v12 with coastal gaps, minus land (sea); Mollweide ESRI:54009",
                 "10": round(res["land_km2"], 2), "11": round(res["marine_km2"], 2), "27": C["timeseries_start"]},
       "setup_note": f"Worked example: real WDPA/WD-OECM October 2026 records for {NAME} ({n_poly} PA polygons, {n_pt} PA points, {n_oe} OECMs). "
                     "Net areas from 03_analysis/scripts/01_gis_flatten.py: points buffered, clipped to land / sea, PAs flattened, "
                     "OECMs PA-erased and flattened, overlaps attributed to the earliest-designated site.",
       "register": reg, "kba": kba, "biomes": biomes, "units": units,
       "inland": [[round(res["rivers_km"], 1), round(res["rivers_in_pa_km"], 1), round(res["rivers_in_oecm_km"], 1)],
                  [round(wl["lakes_wetlands_km2"], 2), round(wl["lakes_wetlands_pa_km2"], 2), round(wl["lakes_wetlands_oecm_km2"], 2)]]}
json.dump(cfg, open(f"{OUT}/tool_config_{NAME.lower()}.json", "w"), indent=1, ensure_ascii=False)
print(len(reg), "register rows;", len(kba), "KBAs;", biomes)
print("PAME rows:", [(r[0], r[1], r[4], r[20], r[21]) for r in reg if r[19] == "Y"])
