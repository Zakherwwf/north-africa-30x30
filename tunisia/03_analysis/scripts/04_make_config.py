"""Assemble the Tunisia configuration for the Indicator 3.1 Excel tool from the GIS outputs."""
import csv, json, os, math
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA, OUT = f"{HERE}/../../01_data", f"{HERE}/../outputs"
MOLL = "ESRI:54009"
t = pd.read_csv(f"{OUT}/sites_net_areas.csv")
pame = json.load(open(f"{DATA}/protected_planet/ProtectedPlanet_TUN_PAME_by_site.json"))

TOOLS = {"Management Effectiveness Tracking Tool (METT)": "METT"}
def latest(d):
    best = None
    for tool, yrs in d.items():
        for y in yrs:
            if best is None or y > best[1]:
                best = (tool, y)
    return best

# evaluations recorded on one record, applied to the record holding the area (same physical site)
# rule from the tool ReadMe: transfer site-level attributes to the record that keeps the area after flattening
TRANSFER = {4322: 941,      # Ichkeul World Heritage Site -> Ichkeul National Park (1980)
            2115: 942,      # Zembra & Zembretta Biosphere Reserve -> Zembra & Zembretta National Park
            13962: 4487,    # Djebel Bou-Hedma Biosphere Reserve -> Bou Hedma National Park
            555624268: 941} # Ichkeul Biosphere Reserve -> Ichkeul National Park
evals = {}   # site_id -> list of (tool, year, source_site)
for sid, d in pame.items():
    sid = int(sid)
    for tool, yrs in list(d.values())[0].items():
        for y in yrs:
            evals.setdefault(TRANSFER.get(sid, sid), []).append((tool, y, sid))

realm_code = {"Terrestrial": 0, "Coastal": 1, "Marine": 2}
t["yr_key"] = t.status_yr.apply(lambda y: y if y and y > 0 else 9999)
t["order"] = t.desig_type.map({"National": 0, "Regional": 1, "International": 2}).fillna(3)
t = t.sort_values(["yr_key", "order", "site_id"])
reg = []
for r in t.itertuples():
    ev = evals.get(r.site_id)
    note = []
    pm = ["N", "", "", "", ""]
    if ev:
        tool, yr, src = max(ev, key=lambda e: e[1])
        pm = ["Y", TOOLS.get(tool, "Other"), int(yr), "", ""]
        note.append("GD-PAME: " + "; ".join(f"{e[0]} {e[1]}" + (f" (from record {e[2]})" if e[2] != r.site_id else "") for e in sorted(ev, key=lambda e: -e[1])))
    if isinstance(r.excluded, str) and r.excluded:
        note.append("Excluded in GIS: " + r.excluded)
    elif r.clip_terr + r.clip_mar > 0 and (r.net_terr + r.net_mar) < 0.9 * (r.clip_terr + r.clip_mar):
        note.append("Overlap attributed to earlier site")
    incl = not (isinstance(r.excluded, str) and r.excluded)
    reg.append([int(r.site_id), r.name_eng, r.desig_eng, r.desig_type, "PA", r.iucn_cat, r.gov_type, r.status,
                int(r.status_yr) if r.status_yr and r.status_yr > 0 else "", realm_code.get(r.realm, 0), r.geom_kind,
                float(r.rep_area), float(r.rep_m_area),
                round(float(r.gis_area), 3) if r.gis_area == r.gis_area else "",
                round(float(r.gis_m_area), 3) if r.gis_m_area == r.gis_m_area else "",
                "Y" if r.desig_eng == "UNESCO-MAB Biosphere Reserve" else "N", "",
                round(r.net_terr, 3) if incl else "", round(r.net_mar, 3) if incl else "",
                *pm, "; ".join(note)])

# ------------------------------------------------------------------ KBAs (official polygons, World Database of KBAs Sept 2026)
# realm flags and PA-covered area computed in 02_kba_overlay.py from the KBA polygons and the flattened PA layer
kc = pd.read_csv(f"{OUT}/kba_coverage_TUN.csv").sort_values("SitRecID")
kba = [[int(r.SitRecID), r.name, round(r.area_km2, 3), round(max(0.0, r.ocean_frac), 3), r.terrestrial, r.freshwater,
        r.mountain, round(r.pa_covered_km2, 3), 0] for r in kc.itertuples()]

# ------------------------------------------------------------------ ecosystems
GET = {"Temperate Conifer Forests": "T2", "Mediterranean Forests, Woodlands & Scrub": "T3",
       "Deserts & Xeric Shrublands": "T5", "Flooded Grasslands & Savannas": "T5"}
eco = pd.read_csv(f"{OUT}/ecoregion_coverage.csv")
eco["get"] = eco.biome.map(GET)
biomes = {g: [round(d.extent_km2.sum(), 2), round(d.pa_km2.sum(), 2), 0] for g, d in eco.groupby("get")}
units = [["Terrestrial ecoregion (Dinerstein et al. 2017)", f"ECO-{r.eco_id}", r.eco_name, r.get, "Y",
          round(r.extent_km2, 2), round(r.pa_km2, 2), 0] for r in eco.itertuples()]
meow = pd.read_csv(f"{OUT}/marine_ecoregion_coverage.csv")
units += [["Marine ecoregion (Spalding et al. 2007)", f"MEOW-{r.eco_code}", r.ecoregion, "", "Y",
           round(r.extent_km2, 2), round(r.pa_km2, 2), 0] for r in meow.itertuples()]
res = json.load(open(f"{OUT}/results.json"))
wl = json.load(open(f"{OUT}/glwd_results.json"))      # 03_wetlands_glwd.py

cfg = {"out": os.path.abspath(f"{HERE}/../../04_tool/GBF_3.1_Tool_Tunisia_Worked_Example.xlsx"),
       "setup": {"4": "Tunisia", "5": "TUN", "6": 2026, "7": "WDPA/WD-OECM October 2026 (Protected Planet; UNEP-WCMC map service)",
                 "8": "World Database of KBAs, September 2026 release (KBAsGlobal_2026_September, 72 Tunisian polygons)",
                 "9": "geoBoundaries ADM0, inland holes filled (land) + Marine Regions EEZ v12 with coastal lagoons, minus land (sea); Mollweide ESRI:54009",
                 "10": round(res["land_km2"], 2), "11": round(res["marine_km2"], 2), "27": 1940},
       "setup_note": "Worked example: real WDPA October 2026 records for Tunisia (137 polygons, 12 points, no OECMs). Net areas from "
                     "03_analysis/scripts/01_gis_flatten.py: points buffered, clipped to land / EEZ, flattened, overlaps attributed to the earliest-designated site.",
       "register": reg, "kba": kba, "biomes": biomes, "units": units,
       "inland": [[round(res["rivers_km"], 1), round(res["rivers_in_pa_km"], 1), 0],
                  [round(wl["lakes_wetlands_km2"], 2), round(wl["lakes_wetlands_pa_km2"], 2), 0]]}
json.dump(cfg, open(f"{OUT}/tool_config_tunisia.json", "w"), indent=1, ensure_ascii=False)
print(len(reg), "register rows;", len(kba), "KBAs;", biomes)
print("PAME rows:", [(r[0], r[1], r[20], r[21]) for r in reg if r[19] == "Y"])
