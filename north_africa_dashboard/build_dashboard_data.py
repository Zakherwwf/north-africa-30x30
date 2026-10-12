"""Assemble the North Africa 30x30 dashboard datasets from the five country folders.

Reads each country's 03_analysis/outputs and writes JSON row files to ./data:
countries, timeseries, sites, kbas, ecoregions, wetlands, governance, effectiveness, narratives, geo.
Headline figures are the Excel-recalculated workbook values (they equal the GIS outputs used here).
"""
import csv, json, os, re
from shapely.geometry import shape
from shapely.ops import unary_union
from shapely.validation import make_valid

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ROOT)
# VARIANT=ws builds the second WWF site (wwf_site_ws), with Morocco including Western Sahara (../morocco_incl_western_sahara)
WS = os.environ.get("VARIANT") == "ws"
OUT = os.path.join(ROOT, "wwf_site_ws", "data") if WS else os.path.join(ROOT, "data")
os.makedirs(OUT, exist_ok=True)

C = [("TUN", "Tunisia", "tunisia"), ("DZA", "Algeria", "algeria"), ("MAR", "Morocco", "morocco"),
     ("LBY", "Libya", "libya"), ("EGY", "Egypt", "egypt")]
if WS:
    C[2] = ("MAR", "Morocco", "morocco_incl_western_sahara")
GUIDES = {"TUN": "https://claude.ai/artifact/GtevPcAkwKc1KA8GWAR8hN", "DZA": "https://claude.ai/artifact/2Ri6py5rvSzYeYL87RjzeK",
          "MAR": "https://claude.ai/artifact/1U1h1sQHhHhCYWfhALQMXS", "LBY": "https://claude.ai/artifact/JVzvhmbkptPRTiggH2fy9i",
          "EGY": "https://claude.ai/artifact/Jg4Cc5CJLg7v7EzzVpBbSE"}
# Protected Planet, October 2026 (country pages) and national documents
PP = {"TUN": dict(pp_land_pa=7.91, pp_land_all=7.91, pp_sea=1.11),
      "DZA": dict(pp_land_pa=4.66, pp_land_all=54.41, pp_sea=0.07),
      "MAR": dict(pp_land_pa=2.14, pp_land_all=33.75, pp_sea=0.31),
      "LBY": dict(pp_land_pa=0.13, pp_land_all=0.13, pp_sea=0.63),
      "EGY": dict(pp_land_pa=13.12, pp_land_all=13.12, pp_sea=5.07)}
NATIONAL = {"TUN": ("7.86% land, 1.1% sea (7th National Report, 2026)", "Add 4% to the protected-area network (national target A3)"),
            "DZA": ("Cultural Parks 43.77% of the territory (7th National Report, 2026)", "50% of land and 5% of sea by 2030"),
            "MAR": ("24.2% in 2025 (7th National Report, national data set)", "30% of land and water by 2030–2035"),
            "LBY": ("About 0.16% of the territory, 11 reserves (NBSAP, 2010 figure)", "30% of the territory by 2030"),
            "EGY": ("14.9% of land and sea, 30 protected areas (NBSAP 2015–2030)", "20% PAs and OECMs by 2030 (NBSAP 2025)")}
BOUNDARY = {"TUN": "geoBoundaries land with coastal lagoons assigned to the sea; Marine Regions EEZ v12.",
            "DZA": "geoBoundaries land; Marine Regions EEZ v12.",
            "MAR": "Western Sahara excluded (land cut at 27°40′N; Moroccan EEZ only), as in Protected Planet.",
            "LBY": "Libyan EEZ only; the Egypt–Libya overlapping claim is not counted.",
            "EGY": "Halaib Triangle excluded from land and sea; with it, 12.81% of land and 4.62% of sea."}
GOV = {"Federal or national ministry or agency": "Government", "Sub-national ministry or agency": "Government",
       "Government-delegated management": "Government", "Transboundary governance": "Shared", "Collaborative governance": "Shared",
       "Joint governance": "Shared", "Individual landowners": "Private", "Non-profit organisations": "Private",
       "For-profit organisations": "Private", "Indigenous peoples": "Indigenous peoples & local communities",
       "Local communities": "Indigenous peoples & local communities", "Not Reported": "Not reported"}


if WS:
    GUIDES = {iso: f"guides/{name.lower()}.html" for iso, name, _ in C}   # the guides bundled with the site
    BOUNDARY["MAR"] = "Western Sahara included (full geoBoundaries outline; Moroccan EEZ plus the Western Sahara zone); Protected Planet excludes it."


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def guide_values(folder):
    """R dict and ts list from the country's guide script (values transcribed from the Excel recalculation)."""
    s = open(os.path.join(BASE, folder, "03_analysis/scripts/06_make_guide.py")).read()
    ts = eval(re.search(r"^ts = (\[.*?\])\n", s, re.S | re.M).group(1))
    return ts


countries, timeseries, sites, kbas, ecos, wets, govs, pames, geo = [], [], [], [], [], [], [], [], []
for iso, name, folder in C:
    o = os.path.join(BASE, folder, "03_analysis/outputs")
    res = json.load(open(f"{o}/results.json"))
    cfg = json.load(open(f"{o}/tool_config_{name.lower()}.json"))
    wl = json.load(open(f"{o}/glwd_results.json"))
    land, sea = cfg["setup"]["10"], cfg["setup"]["11"]
    reg = cfg["register"]
    inc = [r for r in reg if r[17] != ""]
    pa_l = sum(r[17] for r in inc if r[4] == "PA"); oe_l = sum(r[17] for r in inc if r[4] == "OECM")
    pa_s = sum(r[18] for r in inc if r[4] == "PA"); oe_s = sum(r[18] for r in inc if r[4] == "OECM")

    # governance and effectiveness from the register (same rules as the workbook)
    g = {}
    p = {}
    for r in inc:
        k = GOV.get(r[6], "Not reported")
        g.setdefault(k, [0, 0.0, 0.0]); g[k][0] += 1; g[k][1] += r[17]; g[k][2] += r[18]
        yr = r[21] if r[19] == "Y" and r[21] != "" else None
        cls = "Not assessed" if yr is None else ("Assessed, current (no score)" if 2026 - yr <= 5 else "Assessment outdated")
        p.setdefault(cls, [0, 0.0, 0.0]); p[cls][0] += 1; p[cls][1] += r[17]; p[cls][2] += r[18]
    for k, v in g.items():
        govs.append(dict(iso3=iso, country=name, governance=k, sites=v[0], land_km2=round(v[1], 2), sea_km2=round(v[2], 2),
                         share_of_covered_land=round(v[1] / (pa_l + oe_l) * 100, 2) if pa_l + oe_l else 0))
    for k, v in p.items():
        pames.append(dict(iso3=iso, country=name, effectiveness=k, sites=v[0], land_km2=round(v[1], 2), sea_km2=round(v[2], 2),
                          share_of_covered_land=round(v[1] / (pa_l + oe_l) * 100, 2) if pa_l + oe_l else 0))

    # KBAs
    kc = list(csv.DictReader(open(f"{o}/kba_coverage_{iso}.csv")))
    krows = []
    for r in kc:
        a = num(r["area_km2"]); pa = num(r["pa_covered_km2"]); oe = num(r.get("oecm_covered_km2", 0))
        tot = min(100.0, (pa + oe) / a * 100) if a else 0
        krows.append(dict(iso3=iso, country=name, sitrecid=int(r["SitRecID"]), kba=r["name"], area_km2=round(a, 2),
                          ocean_fraction=round(max(0.0, num(r["ocean_frac"])), 3), terrestrial=r["terrestrial"], freshwater=r["freshwater"],
                          mountain=r["mountain"], marine=r["marine"], pa_km2=round(pa, 2), oecm_km2=round(oe, 2),
                          covered_pct=round(tot, 2), pa_only_pct=round(min(100.0, pa / a * 100) if a else 0, 2),
                          coverage_class="Complete" if tot >= 98 else ("Partial" if tot > 0 else "None"),
                          kba_db_pct=num(r["kba_db_pa_cov_pct"]) if r.get("kba_db_pa_cov_pct") not in (None, "", "nan") else None))
    kbas += krows

    def mean(rows, key):
        return round(sum(r[key] for r in rows) / len(rows), 2) if rows else None

    # ecoregions (terrestrial and marine)
    for f, realm, nk in (("ecoregion_coverage.csv", "Land", "eco_name"), ("marine_ecoregion_coverage.csv", "Sea", "ecoregion")):
        for r in csv.DictReader(open(f"{o}/{f}")):
            ext = num(r["extent_km2"])
            if ext < 1:
                continue
            pa, oe = num(r["pa_km2"]), num(r.get("oecm_km2", 0))
            ecos.append(dict(iso3=iso, country=name, realm=realm, ecoregion=r[nk], biome=r.get("biome", "Marine"), extent_km2=round(ext, 1),
                             pa_km2=round(pa, 1), oecm_km2=round(oe, 1), covered_pct=round((pa + oe) / ext * 100, 2)))
    # wetlands
    for r in csv.DictReader(open(f"{o}/glwd_wetland_coverage_by_group.csv")):
        if r["counted"] != "Y" or num(r["extent_km2"]) < 1:
            continue
        ext, pa, oe = num(r["extent_km2"]), num(r["pa_km2"]), num(r.get("oecm_km2", 0))
        wets.append(dict(iso3=iso, country=name, wetland_group=r["group"], extent_km2=round(ext, 1), pa_km2=round(pa, 1), oecm_km2=round(oe, 1),
                         covered_pct=round((pa + oe) / ext * 100, 2)))

    # sites register
    for r in reg:
        excl = r[17] == ""
        sites.append(dict(iso3=iso, country=name, site_id=str(r[0]), site=r[1], designation=r[2], designation_type=r[3], site_type=r[4],
                          iucn=r[5], governance=r[6], status=r[7], year=r[8] if r[8] != "" else None, geometry=r[10],
                          counted="No" if excl else "Yes", exclusion=(r[24].split("Excluded in GIS: ")[-1].split(";")[0] if excl else ""),
                          net_land_km2=None if excl else round(r[17], 2), net_sea_km2=None if excl else round(r[18], 2),
                          effectiveness_year=r[21] if r[19] == "Y" else None))

    # time series (Excel values transcribed in each guide script)
    for t in guide_values(folder):
        y, tot, second, sea_ = t
        pa_only = second if iso in ("DZA", "MAR") else tot
        timeseries.append(dict(iso3=iso, country=name, year=y, land_pct=tot, land_pa_pct=pa_only, sea_pct=sea_))

    kp = PP[iso]
    countries.append(dict(
        iso3=iso, country=name, land_km2=land, sea_km2=sea,
        pa_land_km2=round(pa_l, 2), oecm_land_km2=round(oe_l, 2), covered_land_km2=round(pa_l + oe_l, 2),
        pa_sea_km2=round(pa_s, 2), oecm_sea_km2=round(oe_s, 2), covered_sea_km2=round(pa_s + oe_s, 2),
        land_pct=round((pa_l + oe_l) / land * 100, 2), land_pa_pct=round(pa_l / land * 100, 2), land_oecm_pct=round(oe_l / land * 100, 2),
        sea_pct=round((pa_s + oe_s) / sea * 100, 2),
        land_needed_km2=round(max(0, 0.3 * land - pa_l - oe_l), 0), sea_needed_km2=round(max(0, 0.3 * sea - pa_s - oe_s), 0),
        records=len(reg), counted=len(inc), pa_counted=sum(1 for r in inc if r[4] == "PA"), oecm_counted=sum(1 for r in inc if r[4] == "OECM"),
        excluded=len(reg) - len(inc), point_sites=sum(1 for r in inc if r[10] == "Point"),
        kba_count=len(krows), kba_mean_pct=mean(krows, "covered_pct"), kba_mean_pa_pct=mean(krows, "pa_only_pct"),
        kba_complete=sum(1 for r in krows if r["coverage_class"] == "Complete"), kba_partial=sum(1 for r in krows if r["coverage_class"] == "Partial"),
        kba_none=sum(1 for r in krows if r["coverage_class"] == "None"),
        kba_marine_pct=mean([r for r in krows if r["marine"] == "Y"], "covered_pct"), kba_freshwater_pct=mean([r for r in krows if r["freshwater"] == "Y"], "covered_pct"),
        kba_mountain_pct=mean([r for r in krows if r["mountain"] == "Y"], "covered_pct"),
        rivers_pct=round((res["rivers_in_pa_km"] + res.get("rivers_in_oecm_km", 0)) / res["rivers_km"] * 100, 2),
        wetlands_pct=round((wl["lakes_wetlands_pa_km2"] + wl.get("lakes_wetlands_oecm_km2", 0)) / wl["lakes_wetlands_km2"] * 100, 2),
        gov_not_reported_pct=round(g.get("Not reported", [0, 0, 0])[1] / (pa_l + oe_l) * 100, 2) if pa_l + oe_l else 0,
        pame_current_pct=round(p.get("Assessed, current (no score)", [0, 0, 0])[1] / (pa_l + oe_l) * 100, 2) if pa_l + oe_l else 0,
        pp_land_pa_pct=kp["pp_land_pa"], pp_land_pct=kp["pp_land_all"], pp_sea_pct=kp["pp_sea"],
        national_figure=NATIONAL[iso][0], national_target=NATIONAL[iso][1], base_map=BOUNDARY[iso], guide_url=GUIDES[iso]))

    # ------------------------------------------------------------- map geometry (Mollweide km, simplified)
    gm = json.load(open(f"{o}/geom_moll_simplified.json"))
    kg = json.load(open(f"{o}/kba_geom_moll_simplified.json"))
    pa_keys = ("flat_t", "flat_m") if "flat_t" in gm else ("pa_t", "pa_m")
    oe_keys = () if "flat_t" in gm else ("oe_t", "oe_m")

    def poly(gj):
        try:
            g_ = make_valid(shape(gj))
        except Exception:
            return None
        return None if g_.is_empty else g_

    def path(g_, tol):
        g_ = g_.simplify(tol, preserve_topology=True)
        out = []
        for pg in getattr(g_, "geoms", [g_]):
            if pg.geom_type != "Polygon" or pg.area < (tol * tol * 0.5):
                continue
            for ring in [pg.exterior, *pg.interiors]:
                cs = list(ring.coords)
                if len(cs) < 4:
                    continue
                out.append("M" + "L".join(f"{x/1000:.1f},{-y/1000:.1f}" for x, y in cs) + "Z")
        return "".join(out)

    big = iso in ("DZA", "LBY", "EGY")
    for layer, keys, tol in (("land", ("land",), 2500 if big else 1200), ("sea", ("sea",), 3000 if big else 1500),
                             ("pa", pa_keys, 1500 if big else 600), ("oecm", oe_keys, 2500 if big else 900)):
        parts = [poly(gm[k]) for k in keys if k in gm]
        parts = [x for x in parts if x is not None]
        if not parts:
            continue
        d = path(unary_union(parts), tol)
        if d:
            geo.append(dict(iso3=iso, layer=layer, id=f"{iso}-{layer}", label=name, value=None, d=d))
    for k in kg["kba"]:
        g_ = poly(k["geom"])
        if g_ is None:
            continue
        d = path(g_, 800 if big else 400)
        if not d:
            c = g_.representative_point()
            d = f"M{c.x/1000-1.5:.1f},{-c.y/1000:.1f}a1.5,1.5 0 1,0 3,0a1.5,1.5 0 1,0 -3,0Z"
        kr = next((r for r in krows if r["sitrecid"] == k["id"]), None)
        geo.append(dict(iso3=iso, layer="kba", id=str(k["id"]), label=k["name"], value=kr["covered_pct"] if kr else None, d=d))

for n, rows in (("countries", countries), ("timeseries", timeseries), ("sites", sites), ("kbas", kbas), ("ecoregions", ecos),
                ("wetlands", wets), ("governance", govs), ("effectiveness", pames), ("geo", geo)):
    json.dump(rows, open(f"{OUT}/{n}.json", "w"), ensure_ascii=False, separators=(",", ":"))
    print(f"{n}: {len(rows)} rows, {os.path.getsize(f'{OUT}/{n}.json')/1024:.0f} KB")
for c in countries:
    print({k: c[k] for k in ("iso3", "land_pct", "land_pa_pct", "land_oecm_pct", "sea_pct", "kba_mean_pct", "rivers_pct", "wetlands_pct",
                             "gov_not_reported_pct", "pame_current_pct", "land_needed_km2", "sea_needed_km2")})
