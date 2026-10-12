"""Generate the illustrated Tunisia walkthrough for the Indicator 3.1 tool (numbers from the Excel-recalculated workbook)."""
import json, html, os, re
from shapely.geometry import shape, mapping

HERE = os.path.dirname(os.path.abspath(__file__))
OUTD = f"{HERE}/../outputs"
OUT = os.path.abspath(f"{HERE}/../../05_guide/Tunisia_Indicator_3.1_Guide.html")
geo = json.load(open(f"{OUTD}/geom_moll_simplified.json"))
cfg = json.load(open(f"{OUTD}/tool_config_tunisia.json"))
res = json.load(open(f"{OUTD}/results.json"))
reg = {r[0]: r for r in cfg["register"]}
e = html.escape
CSS = open(f"{HERE}/guide_style.css").read()
kgeo = json.load(open(f"{OUTD}/kba_geom_moll_simplified.json"))
kres = json.load(open(f"{OUTD}/kba_results.json"))
CSS += """
.maps.one{grid-template-columns:minmax(0,1fr)}
.maps.one svg{max-width:520px;margin:0 auto}
.split{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}
@media (max-width:560px){.split{grid-template-columns:minmax(0,1fr)}}
.facts.six{grid-template-columns:repeat(3,minmax(0,1fr))}
@media (max-width:900px){.facts.six{grid-template-columns:repeat(2,minmax(0,1fr))}}
"""

# ------------------------------------------------------------------ verified results (Excel recalculation of 04_tool workbook)
R = dict(land=155616.70, sea=99981.97, pa_t=12344.567, pa_m=1068.346, cov_t=0.079326749635, cov_m=0.010685386575,
         gap_t=22.067325036452, gap_m=28.93146134248, need_t=34340.443, need_m=28926.245,
         gross_t=res["gross_terr"], gross_m=res["gross_mar"],
         kba_all=0.413450925754, kba_m=0.320765300523, kba_f=0.393679448135, kba_mt=0.442192777948,
         govA_t=12300.742, govNR_t=43.825, pame_ns=168.622, pame_old_t=2382.606, pame_old_m=229.29,
         riv=37829.4, riv_in=3717.1)
# (year, terrestrial % with imputation, terrestrial % dated sites only, marine %)
ts = [(1940, 0, 0, 0), (1948, .0536, .0532, .2289), (1949, 3.2659, 3.2651, .2289), (1954, 3.5012, 3.5000, .2289),
      (1966, 3.5435, 3.5420, .2716), (1979, 3.5483, 3.5459, .3287), (1980, 3.8615, 3.8556, .3587), (1993, 3.9891, 3.9748, .3593),
      (1994, 5.1254, 5.1106, .3593), (2001, 5.1275, 5.1112, .5191), (2007, 5.3724, 5.3437, .6787), (2009, 5.4446, 5.4118, .6787),
      (2010, 7.7025, 7.6638, .6790), (2012, 7.8286, 7.7780, 1.0665), (2013, 7.9045, 7.8515, 1.0685), (2021, 7.9327, 7.8793, 1.0685),
      (2026, 7.9327, 7.8793, 1.0685)]


# ------------------------------------------------------------------ SVG maps from real geometries (Mollweide metres)
def rings_raw(g):
    if g["type"] == "Polygon":
        return [g["coordinates"]]
    if g["type"] == "MultiPolygon":
        return g["coordinates"]
    if g["type"] == "GeometryCollection":
        return [p for s in g["geometries"] for p in rings_raw(s)]
    return []


def simp(g, tol):
    return mapping(shape(g).simplify(tol, preserve_topology=True))


land, sea = geo["land"], geo["sea"]
cx = [p for poly in rings_raw(land) + rings_raw(sea) for ring in poly for p in ring]
minx, maxx = min(p[0] for p in cx), max(p[0] for p in cx)
miny, maxy = min(p[1] for p in cx), max(p[1] for p in cx)
W = 420
k = (W - 20) / (maxx - minx)
H = int((maxy - miny) * k + 20)


def path(g):
    out = []
    for poly in rings_raw(g):
        for ring in poly:
            out.append("M" + " L".join(f"{(x - minx) * k + 10:.1f},{(maxy - y) * k + 10:.1f}" for x, y in ring) + "Z")
    return " ".join(out)


colour = {"National": "var(--nat)", "International": "var(--intl)", "Regional": "var(--reg)"}
before = "".join(
    f'<path d="{path(simp(s["geom"], 900))}" fill="{colour.get(s["dtype"], "var(--ink-2)")}" fill-opacity="0.28" '
    f'stroke="{colour.get(s["dtype"], "var(--ink-2)")}" stroke-width="0.6"><title>{e(s["name"])} ({e(s["desig"])})</title></path>'
    for s in geo["sites"])
base = (f'<path d="{path(sea)}" fill="var(--sea)" stroke="var(--sea-line)" stroke-width="0.8"/>'
        f'<path d="{path(land)}" fill="var(--land)" stroke="var(--ink-2)" stroke-width="0.9"/>')
flat = (f'<path d="{path(simp(geo["flat_t"], 600))}" fill="var(--accent)" fill-opacity="0.85" stroke="var(--accent)" stroke-width="0.6"/>'
        f'<path d="{path(simp(geo["flat_m"], 600))}" fill="var(--intl)" fill-opacity="0.85" stroke="var(--intl)" stroke-width="0.6"/>')
scale_km = 100
sb = scale_km * 1000 * k
scalebar = (f'<g font-size="11" fill="var(--ink-2)"><rect x="12" y="{H - 16}" width="{sb:.1f}" height="4" fill="var(--ink-2)"/>'
            f'<text x="{12 + sb + 6:.1f}" y="{H - 11}">{scale_km} km</text></g>')


def svgmap(inner, label):
    return f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{e(label)}">{base}{inner}{scalebar}</svg>'


# ------------------------------------------------------------------ Excel-style sheet mocks
def mock(sheet, cols, rows, note=None):
    h = [f'<figure class="sheet"><figcaption><span class="tab">{e(sheet)}</span>{e(note) if note else ""}</figcaption><div class="scroll"><table class="grid">']
    h.append('<thead><tr><th class="rn"></th>' + "".join(f"<th>{c}</th>" for c, _ in cols) + "</tr>")
    if any(hd for _, hd in cols):
        h.append('<tr class="hdr"><td class="rn"></td>' + "".join(f"<td>{e(hd)}</td>" for _, hd in cols) + "</tr>")
    h.append("</thead><tbody>")
    for rn, cells in rows:
        h.append(f'<tr><td class="rn">{rn}</td>' + "".join(f'<td class="{kk}">{e(str(v))}</td>' for v, kk in cells) + "</tr>")
    h.append("</tbody></table></div></figure>")
    return "".join(h)


def f2(x, d=2):
    return "" if x in ("", None) else (f"{x:,.{d}f}" if isinstance(x, float) else str(x))


setup_rows = [
    (4, "Country / jurisdiction", "Tunisia"), (5, "ISO3 code", "TUN"), (6, "Reporting year", "2026"),
    (7, "WDPA / WD-OECM release used", "WDPA/WD-OECM October 2026"), (8, "KBA dataset version", "World Database of KBAs, September 2026"),
    (9, "Base map used", "geoBoundaries ADM0 + Marine Regions EEZ v12, Mollweide"),
    (10, "Terrestrial area (km²)", "155,616.70"), (11, "Marine & coastal area (km²)", "99,981.97"),
    (12, "Target coverage", "30.0%"), (14, "PA layer flattened in GIS?", "Y"), (15, "OECM layer: PA overlap erased?", "Y  (no OECMs)"),
    (16, "Mollweide equal-area?", "Y"), (17, "Overlaps attributed to earliest site?", "Y"), (26, "PAME validity window (years)", "5"),
    (27, "Time-series start year", "1940")]
setup_mock = mock("Setup", [("A", "Parameter"), ("B", "Value")], [(r, [(l, "lab"), (v, "in")]) for r, l, v in setup_rows], " rows 4–27 (selection)")

# register selection: rows that illustrate every rule
sel = [101835, 903073, 941, 555624267, 17719, 4322, 555624268, 32564, 903071, 12388, 555624277, 109053, 18776, 12391, 15188]
rowno = {r: 5 + i for i, r in enumerate(reg)}
reg_cols = [("A", "SITE_ID"), ("B", "NAME"), ("C", "DESIG_ENG"), ("D", "DESIG_TYPE"), ("H", "STATUS"), ("I", "STATUS_YR"), ("J", "MARINE"),
            ("K", "Geometry"), ("L", "REP_AREA"), ("P", "MAB?"), ("R", "NET terr. km²"), ("S", "NET marine km²"), ("T", "PAME?"),
            ("V", "PAME yr"), ("Z", "Included"), ("AA", "Exclusion reason")]
reg_rows = []
for sid in sel:
    r = reg[sid]
    excl = "STATUS = Proposed" if r[7] == "Proposed" else ("UNESCO-MAB Biosphere Reserve" if r[15] == "Y" else "")
    reg_rows.append((rowno[sid], [(r[0], "in"), (r[1], "in"), (r[2], "in"), (r[3], "in"), (r[7], "in"), (r[8], "in"), (r[9], "in"),
                                  (r[10], "in"), (f2(r[11], 1), "in"), (r[15], "in"), (f2(r[17], 2), "in"), (f2(r[18], 2), "in"),
                                  (r[19], "in"), (r[21], "in"), (0 if excl else 1, "warn" if excl else "calc"), (excl, "warn" if excl else "calc")]))
reg_mock = mock("PA_OECM_Register", reg_cols, reg_rows, " 15 of the 149 real WDPA rows, chosen to show each rule")

head_mock = mock("Headline_3.1", [("A", "Realm"), ("B", "Realm km²"), ("E", "PA used"), ("F", "OECM used"), ("J", "Indicator 3.1"),
                                  ("K", "Target"), ("L", "Gap (pp)"), ("M", "Extra km²"), ("N", "Status")],
                 [(6, [("Terrestrial & inland waters", "lab"), ("155,616.70", "calc"), ("12,344.57", "calc"), ("0.00", "calc"), ("7.93%", "key"),
                       ("30.0%", "calc"), ("22.1", "calc"), ("34,340.44", "calc"), ("Below target", "warn")]),
                  (7, [("Marine & coastal", "lab"), ("99,981.97", "calc"), ("1,068.35", "calc"), ("0.00", "calc"), ("1.07%", "key"),
                       ("30.0%", "calc"), ("28.9", "calc"), ("28,926.25", "calc"), ("Below target", "warn")])], " section A")

kba_sel = [6952, 6919, 6962, 46617, 6942, 46618, 6949, 6955, 6920, 6947, 31736, 31701]
kba_by = {r[0]: r for r in cfg["kba"]}
krow = {r[0]: 16 + i for i, r in enumerate(cfg["kba"])}
kba_rows = []
for sid in kba_sel:
    r = kba_by[sid]
    pct = min(1, r[7] / r[2]) if r[2] else 0
    cls = "Complete" if pct >= 0.98 else ("Partial" if pct > 0 else "None")
    kba_rows.append((krow[sid], [(r[0], "in"), (r[1], "in"), (f2(r[2], 2), "in"), (f2(r[3], 2), "in"), (r[4], "in"), (r[5], "in"), (r[6], "in"),
                                 (f2(r[7], 2), "in"), ("Y" if r[3] >= 0.05 else "N", "calc"), (f"{pct:.1%}", "key"),
                                 (cls, "pass" if cls == "Complete" else ("warn" if cls == "None" else "calc"))]))
kba_mock = mock("KBA_Coverage", [("A", "SitRecID"), ("B", "KBA name"), ("C", "Area km²"), ("D", "Ocean frac."), ("E", "Terr."), ("F", "Freshw."),
                                 ("G", "Mountain"), ("H", "PA-covered km²"), ("J", "Marine?"), ("L", "% covered"), ("O", "Class")],
                kba_rows, " 12 of 72 rows, all values from the KBA polygons")
kba_sum = mock("KBA_Coverage", [("A", "KBA group"), ("B", "SDG"), ("C", "KBAs"), ("D", "Mean % covered"), ("G", "Complete"), ("H", "Partial"), ("I", "None")],
               [(6, [("All KBAs", "lab"), ("—", "calc"), ("72", "calc"), ("41.3%", "key"), ("2", "calc"), ("48", "calc"), ("22", "calc")]),
                (7, [("Terrestrial KBAs", "lab"), ("15.1.2", "calc"), ("71", "calc"), ("41.8%", "key"), ("2", "calc"), ("47", "calc"), ("22", "calc")]),
                (8, [("Freshwater KBAs", "lab"), ("15.1.2", "calc"), ("32", "calc"), ("39.4%", "key"), ("1", "calc"), ("17", "calc"), ("14", "calc")]),
                (9, [("Marine KBAs (≥5% ocean)", "lab"), ("14.5.1", "calc"), ("15", "calc"), ("32.1%", "key"), ("0", "calc"), ("13", "calc"), ("2", "calc")]),
                (10, [("Mountain KBAs", "lab"), ("15.4.1", "calc"), ("13", "calc"), ("44.2%", "key"), ("0", "calc"), ("10", "calc"), ("3", "calc")])],
               " section A (results)")

gov_mock = mock("Governance", [("A", "IUCN governance type"), ("B", "Sites"), ("E", "Terr. km²"), ("G", "% of terr. PA"), ("J", "Marine km²"), ("L", "% of marine PA")],
                [(6, [("A. Governance by government", "lab"), ("137", "calc"), ("12,300.74", "calc"), ("99.6%", "key"), ("1,068.35", "calc"), ("100%", "key")]),
                 (7, [("B. Shared governance", "lab"), ("0", "calc"), ("0.00", "calc"), ("0.0%", "calc"), ("0.00", "calc"), ("0.0%", "calc")]),
                 (8, [("C. Private governance", "lab"), ("0", "calc"), ("0.00", "calc"), ("0.0%", "calc"), ("0.00", "calc"), ("0.0%", "calc")]),
                 (9, [("D. Indigenous peoples & local communities", "lab"), ("0", "calc"), ("0.00", "calc"), ("0.0%", "calc"), ("0.00", "calc"), ("0.0%", "calc")]),
                 (10, [("Not reported", "lab"), ("2", "calc"), ("43.83", "warn"), ("0.4%", "warn"), ("0.00", "calc"), ("0.0%", "calc")]),
                 (11, [("TOTAL", "lab"), ("139", "calc"), ("12,344.57", "calc"), ("100%", "calc"), ("1,068.35", "calc"), ("100%", "calc")])], " section A")

pame_mock = mock("Mgmt_Effectiveness", [("A", "Effectiveness class"), ("B", "Sites"), ("E", "Terr. km²"), ("G", "% of terr. PA"), ("J", "Marine km²"), ("L", "% of marine PA")],
                 [(6, [("High / Moderate / Low (scored)", "lab"), ("0", "calc"), ("0.00", "calc"), ("0.0%", "calc"), ("0.00", "calc"), ("0.0%", "calc")]),
                  (9, [("Assessed – no score (Ichkeul, 2025)", "lab"), ("1", "calc"), ("168.62", "key"), ("1.4%", "key"), ("0.00", "calc"), ("0.0%", "calc")]),
                  (10, [("Assessment outdated (2001–2016)", "lab"), ("10", "calc"), ("2,382.61", "warn"), ("19.3%", "warn"), ("229.29", "warn"), ("21.5%", "warn")]),
                  (11, [("Not assessed", "lab"), ("128", "calc"), ("9,793.34", "calc"), ("79.3%", "calc"), ("839.06", "calc"), ("78.5%", "calc")])], " section A (selection)")

eco_rows = []
for i, u in enumerate(cfg["units"]):
    pct = u[6] / u[5] if u[5] else 0
    eco_rows.append((58 + i, [(u[0].split(" (")[0], "in"), (u[1], "in"), (u[2], "in"), (u[3], "in"), (f2(u[5], 0), "in"), (f2(u[6], 1), "in"),
                              (f"{pct:.1%}", "key"), ("No", "warn")]))
eco_mock = mock("Ecosystems", [("A", "Unit level"), ("B", "Code"), ("C", "Unit name"), ("D", "GET biome"), ("F", "Extent km²"), ("G", "PA km²"),
                               ("J", "Coverage"), ("K", "≥ 30%?")], eco_rows, " section D, ecoregions")
biome_mock = mock("Ecosystems", [("A", "GET"), ("C", "Biome"), ("F", "Extent km²"), ("G", "PA km²"), ("J", "Coverage")],
                  [(7, [("T2", "lab"), ("Temperate-boreal forests and woodlands", "lab"), ("2,647", "in"), ("123.5", "in"), ("4.7%", "key")]),
                   (8, [("T3", "lab"), ("Shrublands and shrub-dominated woodlands", "lab"), ("79,079", "in"), ("1,783.1", "in"), ("2.3%", "key")]),
                   (10, [("T5", "lab"), ("Deserts and semi-deserts", "lab"), ("73,760", "in"), ("10,397.5", "in"), ("14.1%", "key")]),
                   (52, [("Rivers", "lab"), ("Rivers and streams (HydroRIVERS, km)", "lab"), ("37,829", "in"), ("3,717.1", "in"), ("9.8%", "key")]),
                   (53, [("Wetlands", "lab"), ("Lakes and wetlands (GLWD v2, km²)", "lab"), ("12,240", "in"), ("5,724.8", "in"), ("46.8%", "key")])],
                  " sections A and C")

import csv as _csv
_wg = [x for x in _csv.DictReader(open(f"{OUTD}/glwd_wetland_coverage_by_group.csv")) if x["counted"] == "Y"]
wet_mock = mock("GLWD v2 · outputs/glwd_wetland_coverage_by_group.csv",
                [("", "Wetland group (GLWD v2 classes)"), ("", "Extent km²"), ("", "In PAs km²"), ("", "Coverage")],
                [(i + 1, [(x["group"], "lab"), (f2(float(x["extent_km2"]), 1), "calc"), (f2(float(x["pa_km2"]), 1), "calc"),
                          (f'{float(x["pa_pct"]):.1f}%', "key")]) for i, x in enumerate(_wg)]
                + [("Σ", [("Lakes and wetlands → Ecosystems row 53", "lab"), ("12,240.1", "calc"), ("5,724.8", "calc"), ("46.8%", "key")])],
                " GIS output, totals typed into row 53")

qc = [("Realm areas entered", "Both", "PASS"), ("PA layer flattened", "Y", "PASS"), ("Mollweide projection", "Y", "PASS"),
      ("Included sites without flattened net area", "0", "PASS"), ("Terrestrial coverage ≤ 100%", "7.93%", "PASS"),
      ("Marine coverage ≤ 100%", "1.07%", "PASS"), ("Included sites with any QC flag", "29", "WARN"),
      ("Included sites with STATUS_YR missing", "5", "INFO"), ("Included point (buffered) sites", "5", "INFO"),
      ("Share of area with GOV_TYPE not reported", "0.3%", "PASS"), ("Governance total = headline total", "0.000", "PASS"),
      ("KBAs with covered area > KBA area", "0", "PASS"), ("Example (fictional) data present", "0", "PASS")]
qc_mock = mock("QC_Checks", [("B", "Check"), ("C", "Value"), ("D", "Result")],
               [(5 + i, [(a, "lab"), (b, "calc"), (c, c.lower())]) for i, (a, b, c) in enumerate(qc)], " selection of the 20 checks")


# ------------------------------------------------------------------ charts
def gauge(v, label, gap_pp, need):
    w, h, pad = 560, 92, 16
    sx = lambda x: pad + x / 40 * (w - 2 * pad)
    ticks = "".join(f'<line x1="{sx(t):.1f}" x2="{sx(t):.1f}" y1="52" y2="58" stroke="var(--ink-2)"/><text x="{sx(t):.1f}" y="72" text-anchor="middle">{t}%</text>' for t in range(0, 41, 10))
    return f'''<svg viewBox="0 0 {w} {h}" role="img" aria-label="{label} coverage {v:.2f} percent against 30 percent target" class="chart">
<rect x="{pad}" y="20" width="{w - 2 * pad}" height="30" rx="3" fill="var(--track)"/>
<rect x="{pad}" y="20" width="{sx(v) - pad:.1f}" height="30" rx="3" fill="var(--accent)"/>
<rect x="{sx(v):.1f}" y="20" width="{sx(30) - sx(v):.1f}" height="30" fill="var(--gap)" fill-opacity="0.55"/>
<line x1="{sx(30):.1f}" x2="{sx(30):.1f}" y1="12" y2="56" stroke="var(--ink)" stroke-width="2"/>
<text x="{sx(30) + 6:.1f}" y="14" class="lab">Target 30%</text>
<text x="{pad + 4}" y="14" class="lab">{label}</text>
<text x="{sx(v) + 6:.1f}" y="40" class="val">{v:.2f}%</text>
{ticks}<text x="{(sx(v) + sx(30)) / 2:.1f}" y="88" text-anchor="middle" class="lab">gap {gap_pp:.1f} pp = {need:,.0f} km²</text></svg>'''


def bars():
    w, h = 560, 190
    rows = [("Land: sum of site areas", R["gross_t"], "var(--gap)"), ("Land: after flattening", R["pa_t"], "var(--accent)"),
            ("Sea: sum of site areas", R["gross_m"], "var(--gap)"), ("Sea: after flattening", R["pa_m"], "var(--intl)")]
    sx = lambda v: 200 + v / 20000 * (w - 280)
    out = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Gross versus flattened area, land and sea" class="chart">']
    for i, (lab, v, c) in enumerate(rows):
        y = 10 + i * 44
        out.append(f'<text x="190" y="{y + 18}" text-anchor="end" class="lab">{lab}</text>'
                   f'<rect x="200" y="{y}" width="{max(2, sx(v) - 200):.1f}" height="26" rx="2" fill="{c}"/>'
                   f'<text x="{sx(v) + 6:.1f}" y="{y + 18}" class="val">{v:,.0f} km²</text>')
    out.append("</svg>")
    return "".join(out)


def tschart():
    w, h, l, r, t, b = 560, 240, 44, 16, 16, 30
    sx = lambda y: l + (y - 1940) / (2030 - 1940) * (w - l - r)
    sy = lambda v: t + (1 - v / 32) * (h - t - b)
    grid = "".join(f'<line x1="{l}" x2="{w - r}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" stroke="var(--line)"/><text x="{l - 6}" y="{sy(v) + 4:.1f}" text-anchor="end">{v}%</text>' for v in (0, 10, 20, 30))
    xt = "".join(f'<text x="{sx(y):.1f}" y="{h - 10}" text-anchor="middle">{y}</text>' for y in (1940, 1960, 1980, 2000, 2020))

    def step(idx):
        pts = []
        for i, row in enumerate(ts):
            if i:
                pts.append(f"{sx(row[0]):.1f},{sy(ts[i - 1][idx]):.1f}")
            pts.append(f"{sx(row[0]):.1f},{sy(row[idx]):.1f}")
        return " ".join(pts)
    area = f"{sx(1940):.1f},{sy(0):.1f} " + step(1) + f" {sx(2026):.1f},{sy(0):.1f}"
    return f'''<svg viewBox="0 0 {w} {h}" role="img" aria-label="Coverage over time 1940 to 2026, land and sea" class="chart">{grid}{xt}
<line x1="{l}" x2="{w - r}" y1="{sy(30):.1f}" y2="{sy(30):.1f}" stroke="var(--ink)" stroke-dasharray="5 4"/>
<text x="{w - r}" y="{sy(30) - 6:.1f}" text-anchor="end" class="lab">30% by 2030</text>
<polygon points="{area}" fill="var(--accent)" fill-opacity="0.14"/>
<polyline points="{step(2)}" fill="none" stroke="var(--ink-2)" stroke-width="1.2" stroke-dasharray="3 3"/>
<polyline points="{step(1)}" fill="none" stroke="var(--accent)" stroke-width="2.5"/>
<polyline points="{step(3)}" fill="none" stroke="var(--intl)" stroke-width="2.5"/>
<circle cx="{sx(2026):.1f}" cy="{sy(7.9327):.1f}" r="4" fill="var(--accent)"/>
<text x="{sx(2026) - 8:.1f}" y="{sy(7.9327) - 10:.1f}" text-anchor="end" class="val">land 7.93%</text>
<circle cx="{sx(2026):.1f}" cy="{sy(1.0685):.1f}" r="4" fill="var(--intl)"/>
<text x="{sx(2026) - 8:.1f}" y="{sy(1.0685) + 16:.1f}" text-anchor="end" class="val" style="fill:var(--intl)">sea 1.07%</text>
<text x="{sx(1949) + 4:.1f}" y="{sy(3.27) - 8:.1f}" class="lab">1949: Chott Jrid</text>
<text x="{sx(1994) - 4:.1f}" y="{sy(5.13) - 8:.1f}" text-anchor="end" class="lab">1994: Jebil NP</text>
<text x="{sx(2010) - 4:.1f}" y="{sy(7.70) - 18:.1f}" text-anchor="end" class="lab">2010: 15 parks and reserves</text></svg>'''


legend = ('<ul class="legend"><li><i style="background:var(--nat)"></i>National (parks, reserves, wetland zones)</li>'
          '<li><i style="background:var(--intl)"></i>International (Ramsar, World Heritage)</li><li><i style="background:var(--reg)"></i>Regional (SPAMI, Barcelona Convention)</li></ul>')
legend2 = ('<ul class="legend"><li><i style="background:var(--accent)"></i>Counted on land</li>'
           '<li><i style="background:var(--intl)"></i>Counted at sea</li><li><i style="background:var(--sea);border:1px solid var(--sea-line)"></i>EEZ (marine denominator)</li></ul>')

CSS = CSS.replace("--land:#e7ece9;", "--land:#e7ece9; --sea:#e3eef6; --sea-line:#b8cfe0;")
CSS = CSS.replace("--land:#1f2c2a;", "--land:#1f2c2a; --sea:#16222c; --sea-line:#2e4555;")

steps = [
    ("data", "Collect the data"), ("setup", "Fill in Setup"), ("gis", "Flatten the overlaps in GIS"), ("register", "Enter the site register"),
    ("headline", "Read the headline"), ("eco", "Ecosystems and inland waters"), ("kba", "Key Biodiversity Areas"), ("gov", "Governance"),
    ("pame", "Management effectiveness"), ("ts", "Time series"), ("qc", "Quality checks and reconciliation"), ("report", "Report"),
    ("gaps", "What this example leaves out")]
nav = "".join(f'<li><a href="#{a}"><span>{i + 1:02d}</span>{e(t)}</a></li>' for i, (a, t) in enumerate(steps))


def head(i, title, sheet=None):
    chip = f'<span class="chip">{e(sheet)}</span>' if sheet else ""
    return f'<section class="step" id="{steps[i][0]}"><div class="stephead"><span class="num">STEP {i + 1:02d}</span>{chip}</div><h2>{e(title)}</h2>'


cellkey = ('<div class="cellkey"><span><i style="background:var(--in-bg)"></i>Input you type or paste</span>'
           '<span><i style="background:var(--calc-bg)"></i>Formula, computed by the tool</span>'
           '<span><i style="background:var(--key-bg)"></i>Key result</span><span><i style="background:var(--warn-bg)"></i>Flag to act on</span></div>')



# ------------------------------------------------------------------ KBA coverage map (official KBA polygons)
def kcol(p):
    if p >= 98:
        return "var(--accent)"
    if p >= 50:
        return "var(--kmid)"
    if p > 0:
        return "var(--gap)"
    return "var(--kzero)"


kpaths = "".join(
    f'<path d="{path(k["geom"])}" fill="{kcol(k["pct"])}" fill-opacity="0.9" stroke="var(--ink)" stroke-width="0.4">'
    f'<title>{e(k["name"])}: {k["pct"]:.1f}% covered</title></path>' for k in sorted(kgeo["kba"], key=lambda k: -k["pct"]))
flat_ghost = (f'<path d="{path(simp(geo["flat_t"], 600))}" fill="none" stroke="var(--ink-2)" stroke-width="0.5" stroke-dasharray="2 2"/>'
              f'<path d="{path(simp(geo["flat_m"], 600))}" fill="none" stroke="var(--ink-2)" stroke-width="0.5" stroke-dasharray="2 2"/>')
klegend = ('<ul class="legend"><li><i style="background:var(--accent)"></i>Complete (≥ 98%)</li><li><i style="background:var(--kmid)"></i>50–98%</li>'
           '<li><i style="background:var(--gap)"></i>Under 50%</li><li><i style="background:var(--kzero)"></i>Not covered</li>'
           '<li><i style="border:1px dashed var(--ink-2);background:none"></i>Protected areas (flat layer)</li></ul>')
CSS = CSS.replace("--land:#e7ece9;", "--land:#e7ece9; --kmid:#c9a93a; --kzero:#b23b3b;")
CSS = CSS.replace("--land:#1f2c2a;", "--land:#1f2c2a; --kmid:#e0c45e; --kzero:#e06a6a;")

body = f"""
<div class="wrap">
<nav class="index" aria-label="Steps"><p class="lbl">Walkthrough</p><ol>{nav}</ol></nav>
<main>
<header class="hero">
<div class="eyebrow">GBF Headline Indicator 3.1 · National worked example with real data</div>
<h1>Tunisia, step by step through the 30×30 tool</h1>
<p class="lede">This guide fills the Indicator 3.1 Excel tool for Tunisia from the 149 records in the October 2026 World Database on Protected Areas, the 72 official Key Biodiversity Area polygons (September 2026), and a GIS run over land and sea. Every number comes from those data and from the workbook recalculated in Excel.</p>
<p>Tunisia has both realms, so the tool reports land and sea separately. It has point sites to buffer, biosphere reserves and proposed sites to exclude, and heavy double-listing: most wetlands appear once as a national wetland zone and again as a Ramsar site. It is also far from the target: under 8% on land and about 1% at sea.</p>
<div class="facts six">
<div><b>149</b><small>WDPA records (137 polygons, 12 points), 0 OECMs</small></div>
<div><b>139</b><small>records counted after filtering</small></div>
<div><b>19,103 km²</b><small>land, summed site by site</small></div>
<div><b>12,345 km²</b><small>land actually covered, overlaps removed</small></div>
<div><b>7.93%</b><small>of 155,617 km² of land</small></div>
<div><b>1.07%</b><small>of 99,982 km² of sea</small></div>
</div>
</header>

{head(0, "Collect the data")}
<p>Everything used here is in the <code>tunisia/01_data</code> folder, with the source of each file:</p>
<ol class="do">
<li><b>Protected areas and OECMs.</b> The WDPA and WD-OECM, October 2026, from the UNEP-WCMC map service behind <a href="https://www.protectedplanet.net/country/TUN">Protected Planet</a>: 137 polygons and 12 points, saved as shapefile, GeoJSON and GeoPackage. Tunisia reports no OECMs.</li>
<li><b>Base map.</b> Land: the geoBoundaries ADM0 outline. Sea: the Marine Regions EEZ v12, Tunisia's 200-nautical-mile zone. Both projected to Mollweide.</li>
<li><b>Key Biodiversity Areas.</b> The World Database of KBAs, September 2026 release: the 72 Tunisian polygons, extracted from the global file, plus their 381 trigger-species records. The KBA data are licensed for this use by the KBA Partnership; don't republish the polygons.</li>
<li><b>Management effectiveness.</b> The GD-PAME evaluations shown on each of the 149 site pages on Protected Planet: 14 sites carry at least one evaluation.</li>
<li><b>Ecosystems, mountains and inland waters.</b> RESOLVE Ecoregions 2017, Marine Ecoregions of the World, the GMBA Mountain Inventory v2.0, HydroRIVERS v1.0 and the Global Lakes and Wetlands Database v2 (GLWD v2, 33 wetland classes), all clipped to Tunisia.</li>
</ol>

{head(1, "Fill in Setup", "Sheet: Setup")}
<p>Setup holds the two denominators and your declarations about the GIS method. Two details of the base map matter here:</p>
<ol class="do">
<li><b>Coastal lagoons.</b> Lac de Tunis, Halk El Menzel, the Kneiss flats and similar lagoons lie between the geoBoundaries coastline and the inner edge of the EEZ, so at first they belonged to neither realm. That dropped 40 km² of protected lagoon. The script closes these gaps, keeps only the pieces that touch the sea (113 km²), and adds them to the marine and coastal realm.</li>
<li><b>Inland waters.</b> Lakes cut out of the land outline (11 km²) are filled back in, since inland waters belong to the terrestrial realm.</li>
</ol>
{setup_mock}
{cellkey}
<p>Rows 14 to 17 each feed a QC check, so the workbook can't claim a flattened, equal-area result unless you declare it. Row 27 starts the time series at 1940, just before Tunisia's first dated site (Bahiret El Bibane, 1948).</p>

{head(2, "Flatten the overlaps in GIS", "Outside Excel: 03_analysis/scripts/01_gis_flatten.py")}
<p>Excel can't do this step, and in Tunisia it removes more than a third of the area. Of the 139 records counted, 48 lose all their area once overlaps are removed, because they describe ground already listed under another designation. Chott Jrid is listed twice: as a 1949 national wetland zone and a 2007 Ramsar site, each about 5,000 km². Ichkeul is listed five times.</p>
<div class="maps">
<figure><figcaption><b>Before: 139 overlapping records</b>Stacked records over the same ground (darker means more overlap)</figcaption>{svgmap(before, "Overlapping protected-area records in Tunisia")}{legend}</figure>
<figure><figcaption><b>After: one flat layer per realm</b>12,345 km² on land and 1,068 km² at sea, each counted once</figcaption>{svgmap(flat, "Flattened protected-area layer in Tunisia")}{legend2}</figure>
</div>
{bars()}
<h3>The procedure (metadata steps 1–6)</h3>
<ol class="do">
<li><b>Filter.</b> Ten records drop out: 7 points with status <i>Proposed</i> (including Jenein-oued Ouni, 3,600 km², and Lac Bizerte) and 3 UNESCO biosphere reserves (Ichkeul, Zembra and Zembretta, Djebel Bou-Hedma). The method excludes biosphere reserves because their buffer and transition zones are not managed for conservation; their cores are counted through the national parks.</li>
<li><b>Buffer points.</b> Five designated points become circles with the reported area. The coastal point Hamada-Sidi Toui (120 km²) spills 42 km² into the sea: the record says terrestrial, but a circle can't follow a coastline. This is why the metadata treats buffered points as approximate.</li>
<li><b>Clip and project.</b> Each site is split into a land part and a sea part, then measured in Mollweide (<code>ESRI:54009</code>).</li>
<li><b>Dissolve.</b> Land: 19,103 km² summed becomes <b>12,344.57 km²</b>. Sea: 2,018 km² becomes <b>1,068.35 km²</b>. The script lists the 69 overlapping pairs in <code>overlap_pairs.csv</code>.</li>
<li><b>Attribute overlaps.</b> Each overlap goes to the earliest-designated site, and ties go to the largest outline. The 1949 Chott Jrid wetland zone keeps 4,998 km² and the 2007 Ramsar record keeps nothing. For Ichkeul, all four counted records date from 1980, so the national park (168.6 km²) holds the area. The per-site net areas add up exactly to the dissolved totals.</li>
</ol>

{head(3, "Enter the site register", "Sheet: PA_OECM_Register")}
<p>All 149 records go in, including the excluded ones; the tool applies the filters itself and says why. Paste the WDPA attributes into the yellow columns and the net land and sea areas from the GIS run into columns R and S.</p>
{reg_mock}
<p>The register shows each rule at work. Proposed points and biosphere reserves get <code>Included = 0</code> with a reason. The second Chott Jrid and Bahiret El Bibane records carry 0 km² net. Sidi Toui National Park has no designation year, so the time series has to impute one.</p>

{head(4, "Read the headline", "Sheet: Headline_3.1")}
<p>Indicator 3.1 is the PA area plus the OECM area, overlaps removed, divided by the realm area, for each realm separately. Key Biodiversity Areas don't count towards it: a KBA is a scientific label, not a protection measure. It counts only once it is designated as a protected area or recognised as an OECM.</p>
{head_mock}
{gauge(7.9326749635, "Land", R["gap_t"], R["need_t"])}
{gauge(1.0685386575, "Sea", R["gap_m"], R["need_m"])}
<div class="result"><div><strong>Result.</strong> Protected areas cover <b>7.93%</b> of Tunisia's land and <b>1.07%</b> of its waters. Reaching 30% would take another <b>34,340 km²</b> on land and <b>28,926 km²</b> at sea. With no OECMs reported, protected areas are the only contributor so far.</div></div>
<p>A single site carries much of the land figure. Chott Jrid, a salt lake, accounts for 4,998 km², or 40% of all protected land. Without it, coverage would be 4.7%.</p>

{head(5, "Ecosystems and inland waters", "Sheet: Ecosystems")}
<p>The metadata asks whether coverage is ecologically representative. Here the flat layer from Step 3 was intersected with the six RESOLVE ecoregions on land and the three marine ecoregions at sea.</p>
{eco_mock}
<p>Ecoregions are then grouped into IUCN Global Ecosystem Typology biomes. The crosswalk is approximate and stated in the config: Mediterranean conifer forests become T2, Mediterranean woodlands and steppe T3, and the Saharan ecoregions T5. River coverage comes from HydroRIVERS: 3,717 of 37,829 km of river lie inside protected areas.</p>
<h3>Lakes and wetlands (script 03_wetlands_glwd.py)</h3>
<p>GLWD v2 maps 33 classes of lakes, rivers and wetlands on a grid of about 500 m, giving the area of each class in every cell. The script measures how much of each cell lies on land and inside the flat protected-area layer, using a 10 × 10 sub-grid per cell, and multiplies by the class areas. River channels (classes 4, 5 and 7) are left out because the rivers row already counts them by length; rice paddies are left out as an artificial system.</p>
{wet_mock}
{biome_mock}
<div class="result"><div><strong>Finding.</strong> Coverage is skewed towards the desert and its salt flats. The Saharan halophytics ecoregion, which holds the chotts, is 51% protected, and 63% of Tunisia's salt pans lie in protected areas. The Mediterranean woodlands and forests of the north, Tunisia's largest ecoregion at 64,145 km², are 2.3% protected. Freshwater habitats fare poorly too: 5% of riverine wetlands, 1% of marshes and 10% of river length. The Ionian Sea part of the EEZ has no protected area at all.</div></div>

{head(6, "Key Biodiversity Areas", "Sheet: KBA_Coverage · script 02_kba_overlay.py")}
<p>The metadata disaggregation is the mean percentage of each KBA covered by protected areas or OECMs. With the official polygons, every column of the KBA sheet comes from GIS: each KBA is overlaid with the same flat layer as the headline.</p>
<div class="maps one"><figure><figcaption><b>72 KBAs by share protected</b>Official KBA polygons, September 2026, against the flattened protected-area layer</figcaption>{svgmap(flat_ghost + kpaths, "Key Biodiversity Areas of Tunisia coloured by protected share")}{klegend}</figure></div>
<h3>How each column is filled</h3>
<ol class="do">
<li><b>Area and covered area</b> (C, H): KBA polygon area in Mollweide, and its intersection with the flat layer.</li>
<li><b>Ocean fraction</b> (D): the share of the polygon outside the land realm. At 5% or more the KBA counts as marine (SDG 14.5.1), as the metadata specifies.</li>
<li><b>Terrestrial</b> (E): at least 5% of the polygon on land (SDG 15.1.2).</li>
<li><b>Freshwater</b> (F): the factsheet lists a freshwater system, the site is a dam, river, garaet or spring, or a trigger species is a freshwater fish, amphibian or dragonfly. Steppe de Gafsa, for example, is triggered by the spring-dwelling cichlid <i>Haplochromis desfontainii</i>.</li>
<li><b>Mountain</b> (G): at least 5% of the polygon inside the GMBA Mountain Inventory v2.0 (SDG 15.4.1). This threshold is a national choice; record it in your report.</li>
</ol>
{kba_mock}
{kba_sum}
<div class="result"><div><strong>Finding.</strong> On average, Tunisia's KBAs are <b>41.3%</b> covered. Only Sidi Toui and Garaet Sejnane are fully covered; Ichkeul (97.8%) and Jebel El Ghorra (97.3%) fall just short of the 98% line. Twenty-two KBAs have no protection at all, among them the Gafsa steppe (244 km²), Jbel Zaghouan (158 km²), the Kuriat Islands (36 km²) and Jbel el Haouaria.</div></div>
<p>The largest unprotected KBA areas are at sea and on the coast: 1,334 km² of the Zembra archipelago, 473 km² of Djerba and 321 km² of the Thyna salt pans. On land, the Maden River KBA (733 km²) and the 1,165 km² of Chott Djerid outside the protected wetland stand out. The layer <code>KBA_unprotected_parts_TUN.shp</code> maps these gaps for planning new sites or OECMs.</p>
<p>The polygon results match the KBA database's own coverage figures for 70 of the 72 KBAs, which confirms the flat layer. The two differences: Sebkhet Ariana is 72% covered here because a buffered point site sits on it, which the KBA database doesn't count; and El Bibane differs by one point. Four foreign KBAs, in Algeria, Libya and Italy, touch Tunisian land or waters by 0.1–10 km² along the borders. They are listed in <code>kba_foreign_overlapping_TUN.csv</code> but not counted.</p>

{head(7, "Governance", "Sheet: Governance")}
{gov_mock}
<div class="result"><div><strong>Finding.</strong> All but 0.4% of the protected area is governed by a national ministry. No shared, private or community-governed sites are reported, so the "equitably governed" element of Target 3 can't be shown from the WDPA. The QC check passes because less than 5% of the area is unreported.</div></div>

{head(8, "Management effectiveness", "Sheet: Mgmt_Effectiveness")}
<p>Fourteen site pages on Protected Planet list GD-PAME evaluations: METT assessments of national parks (2003–2016), biosphere-reserve evaluations (BREMi, 2013), BirdLife IBA monitoring (2001) and IUCN World Heritage Outlook reports for Ichkeul (2014 to 2025).</p>
<div class="pitfall"><h3>Pitfall: evaluations stranded on records that lost their area</h3>
<p>Ichkeul's most recent evaluation, the 2025 World Heritage Outlook, sits on the World Heritage record, which keeps 0.5 km² after flattening. Three BREMi evaluations sit on biosphere-reserve records that are excluded altogether. Left as they are, these evaluations would count for almost nothing.</p>
<p>The rule: when overlapping records describe the same physical site, move site-level attributes to the record that holds the area. Here they went to Ichkeul National Park (941), Zembra and Zembretta National Park (942) and Bou Hedma National Park (4487). Column Y records each move.</p></div>
{pame_mock}
<p>The assessed total is 2,551 km² on land and 229 km² at sea, matching Protected Planet's 2,543 and 229 km². Only Ichkeul has an evaluation from the last five years, and none has a numeric score, so none can be classed High, Moderate or Low. Report this breakdown as provisional.</p>

{head(9, "Time series", "Sheet: Time_Series")}
<p>The tool adds up each site's net area by designation year. Five included sites have no year, among them Sidi Toui National Park. The metadata assigns them random years from the country's other sites and takes the median of 1,000 draws; the tool uses the expected value. The dashed line counts dated sites only.</p>
{tschart()}
<p>Most of the land figure comes from three moments: Chott Jrid in 1949, Jebil National Park in 1994, and 15 national parks and nature reserves gazetted in 2010, including Sanghr Jabbess (2,815 km²). Marine coverage stepped up in 2012 with the Boughrara lagoon. Since 2013 the curve is almost flat. The 7th National Report says the same: little progress since 2010.</p>

{head(10, "Quality checks and reconciliation", "Sheet: QC_Checks")}
{qc_mock}
<p>The one warning covers 29 flagged sites. Most flags compare the WDPA's own realm field with the GIS split: a "terrestrial" point whose circle reaches the sea, or a "marine" lagoon whose edge falls on land. These are expected with two independent base maps. Review them, but they don't change the headline. The rest are five missing designation years and two missing governance types.</p>
<div class="scroll"><table class="recon"><thead><tr><th></th><th>Land km²</th><th>Land %</th><th>Sea km²</th><th>Sea %</th></tr></thead><tbody>
<tr><td>This workbook (geoBoundaries + Marine Regions EEZ)</td><td>12,345 of 155,617</td><td>7.93%</td><td>1,068 of 99,982</td><td>1.07%</td></tr>
<tr><td>Protected Planet, October 2026</td><td>12,278 of 155,146</td><td>7.91%</td><td>1,104 of 99,744</td><td>1.11%</td></tr>
<tr><td>Tunisia's 7th National Report (2026)</td><td>–</td><td>7.86%</td><td>–</td><td>1.1%</td></tr>
<tr><td>Tunisia's 6th National Report (2019)</td><td>–</td><td>about 6%</td><td>–</td><td>–</td></tr>
</tbody></table></div>
<p>The three current figures agree within 0.07 points on land and 0.04 points at sea. The remaining differences come from the coastline: geoBoundaries puts 471 km² more on land than UNEP-WCMC's base map, which moves parts of the coastal lagoons from the sea column to the land column. To match Protected Planet exactly, use its base map or type its totals into Setup rows 18–21 and let QC show the difference.</p>

{head(11, "Report", "Sheet: Dashboard")}
<p>The Dashboard gathers the figures for the national report. A draft paragraph built only from the workbook:</p>
<blockquote class="draft">In 2026, protected areas covered 12,345 km², or 7.93% of Tunisia's terrestrial and inland water area, and 1,068 km², or 1.07% of its marine and coastal area (Headline Indicator 3.1; WDPA October 2026; Mollweide equal-area). No OECMs have been reported. Reaching the 30% element of Target 3 would require a further 34,340 km² on land and 28,926 km² at sea. On average, Tunisia's 72 Key Biodiversity Areas are 41.3% covered (marine KBAs 32.1%, mountain KBAs 44.2%); 22 have no coverage. Coverage ranges from 2.3% of Mediterranean woodlands to 14.1% of deserts; 46.8% of lake and wetland area and 9.8% of river length lie within protected areas. All reported protected area is government-governed, and 21% of it has a management-effectiveness evaluation, almost all older than five years.</blockquote>

{head(12, "What this example leaves out")}
<ol class="do">
<li><b>National wetland inventory.</b> GLWD v2 is a global 500 m product; small wetlands such as the dam lakes and peat bogs of the north are only partly captured. A national wetland map, if one exists, would sharpen the lakes-and-wetlands figure.</li>
<li><b>Marine biomes.</b> Splitting the sea into shelf (M1) and pelagic (M2) needs bathymetry. The marine ecoregions are entered in section D without a biome.</li>
<li><b>Effectiveness scores.</b> GD-PAME gives the method and year, not the score. The scores have to come from the agencies that ran the assessments.</li>
<li><b>National sites not in the WDPA.</b> The 7th National Report plans to extend the network by 4%, including biosphere reserves and sensitive steppe areas. Sites designated but not yet reported to UNEP-WCMC are missing here.</li>
</ol>

<h3>Sources</h3>
<ul class="sources">
<li>UNEP-WCMC &amp; IUCN (2026). <a href="https://www.protectedplanet.net/country/TUN">Protected Planet: Tunisia</a>, WDPA/WD-OECM October 2026, and GD-PAME records on each site page.</li>
<li>GBF Indicators. <a href="https://www.gbf-indicators.org/metadata/headline/3-1">Metadata for Headline Indicator 3.1</a>.</li>
<li>BirdLife International on behalf of the KBA Partnership (2026). World Database of Key Biodiversity Areas, September 2026 release, and KBA trigger species.</li>
<li>République Tunisienne (2026). 7th National Report to the Convention on Biological Diversity; (2019) 6th National Report.</li>
<li>Flanders Marine Institute (2023). Maritime Boundaries Geodatabase, EEZ v12. marineregions.org.</li>
<li>Runfola, D. et al. (2020). geoBoundaries. PLoS ONE 15(4): e0231866.</li>
<li>Snethlage, M.A. et al. (2022). GMBA Mountain Inventory v2. Scientific Data 9: 149.</li>
<li>Dinerstein, E. et al. (2017). An ecoregion-based approach to protecting half the terrestrial realm. BioScience 67(6): 534–545. Spalding, M.D. et al. (2007). Marine ecoregions of the world. BioScience 57(7): 573–583.</li>
<li>Lehner, B. &amp; Grill, G. (2013). HydroSHEDS / HydroRIVERS v1.0. Hydrological Processes 27(15): 2171–2186.</li>
<li>Lehner, B. et al. (2025). Mapping the world's inland surface waters: an upgrade to the Global Lakes and Wetlands Database (GLWD v2). Earth System Science Data 17: 2277–2329.</li>
</ul>
<footer>Files: tunisia/04_tool/GBF_3.1_Tool_Tunisia_Worked_Example.xlsx (filled tool), with the data, scripts, outputs and documents in the same tunisia folder. GIS run with geopandas 1.2, shapely 2 and pyproj; workbook recalculated in Microsoft Excel with zero formula errors.</footer>
</main>
</div>
"""

page = f"""<title>Tunisia Indicator 3.1 Walkthrough</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..800&family=IBM+Plex+Mono:wght@400;500&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">
<style>{CSS}</style>
{body}"""
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w").write(page)
print("written", OUT, len(page))
