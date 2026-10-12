"""Generate the illustrated Algeria walkthrough for the Indicator 3.1 tool (numbers from the Excel-recalculated workbook)."""
import csv, json, html, os
from shapely.geometry import shape, mapping

HERE = os.path.dirname(os.path.abspath(__file__))
OUTD = f"{HERE}/../outputs"
OUT = os.path.abspath(f"{HERE}/../../05_guide/Algeria_Indicator_3.1_Guide.html")
geo = json.load(open(f"{OUTD}/geom_moll_simplified.json"))
kgeo = json.load(open(f"{OUTD}/kba_geom_moll_simplified.json"))
cfg = json.load(open(f"{OUTD}/tool_config_algeria.json"))
reg = {r[0]: r for r in cfg["register"]}
e = html.escape
CSS = open(f"{HERE}/guide_style.css").read()
CSS = CSS.replace("--land:#e7ece9;", "--land:#e7ece9; --sea:#e3eef6; --sea-line:#b8cfe0; --oecm:#c08a2b; --kmid:#c9a93a; --kzero:#b23b3b;")
CSS = CSS.replace("--land:#1f2c2a;", "--land:#1f2c2a; --sea:#16222c; --sea-line:#2e4555; --oecm:#e0b45a; --kmid:#e0c45e; --kzero:#e06a6a;")
CSS += """
.maps.one{grid-template-columns:minmax(0,1fr)}
.maps.one svg{max-width:520px;margin:0 auto}
.facts.six{grid-template-columns:repeat(3,minmax(0,1fr))}
@media (max-width:900px){.facts.six{grid-template-columns:repeat(2,minmax(0,1fr))}}
"""

# ------------------------------------------------------------------ verified results (Excel recalculation of 04_tool workbook)
R = dict(land=2318644.15, sea=131439.54, pa_t=107763.963, oe_t=1151696.347, tot_t=1259460.31, pa_m=89.779,
         cov_pa=0.046477146137, cov_oe=0.496711126198, cov_t=0.543188272336, cov_m=0.0006830440824732,
         gap_m=29.931695591753, need_m=39342.083)
# (year, land % with OECMs, land % PAs only, sea %)
ts = [(1940, 0, 0, 0), (1972, 2.7226, 0, 0), (1982, 5.9840, 3.2614, 0), (1983, 6.0398, 3.3172, .0005), (1984, 6.0542, 3.3316, .0008),
      (1987, 29.4634, 3.3316, .0008), (2001, 30.2743, 4.1425, .0038), (2003, 30.6865, 4.5547, .0243), (2004, 30.7561, 4.6243, .0272),
      (2005, 30.7561, 4.6243, .0342), (2008, 54.2954, 4.6243, .0342), (2011, 54.3080, 4.6369, .0357), (2019, 54.3188, 4.6477, .0683),
      (2026, 54.3188, 4.6477, .0683)]


# ------------------------------------------------------------------ SVG maps
def rings(g):
    if g["type"] == "Polygon":
        return [g["coordinates"]]
    if g["type"] == "MultiPolygon":
        return g["coordinates"]
    if g["type"] == "GeometryCollection":
        return [p for s in g["geometries"] for p in rings(s)]
    return []


def simp(g, tol):
    return mapping(shape(g).simplify(tol, preserve_topology=True))


cx = [p for poly in rings(geo["land"]) + rings(geo["sea"]) for ring in poly for p in ring]
minx, maxx, miny, maxy = min(p[0] for p in cx), max(p[0] for p in cx), min(p[1] for p in cx), max(p[1] for p in cx)
W = 420
k = (W - 20) / (maxx - minx)
H = int((maxy - miny) * k + 20)


def path(g):
    return " ".join("M" + " L".join(f"{(x - minx) * k + 10:.1f},{(maxy - y) * k + 10:.1f}" for x, y in ring) + "Z"
                    for poly in rings(g) for ring in poly)


colour = {"National": "var(--nat)", "International": "var(--intl)", "Regional": "var(--reg)"}
before = "".join(
    f'<path d="{path(simp(s["geom"], 3000))}" fill="{"var(--oecm)" if s["ptype"] == "OECM" else colour.get(s["dtype"], "var(--ink-2)")}" '
    f'fill-opacity="0.3" stroke="{"var(--oecm)" if s["ptype"] == "OECM" else colour.get(s["dtype"], "var(--ink-2)")}" stroke-width="0.6">'
    f'<title>{e(s["name"])} ({e(s["desig"])}, {s["ptype"]})</title></path>' for s in sorted(geo["sites"], key=lambda s: s["ptype"] != "OECM"))
base = (f'<path d="{path(geo["sea"])}" fill="var(--sea)" stroke="var(--sea-line)" stroke-width="0.8"/>'
        f'<path d="{path(geo["land"])}" fill="var(--land)" stroke="var(--ink-2)" stroke-width="0.9"/>')
flat = (f'<path d="{path(simp(geo["oe_t"], 2500))}" fill="var(--oecm)" fill-opacity="0.75" stroke="var(--oecm)" stroke-width="0.5"/>'
        f'<path d="{path(simp(geo["pa_t"], 1500))}" fill="var(--accent)" fill-opacity="0.9" stroke="var(--accent)" stroke-width="0.5"/>'
        f'<path d="{path(geo["pa_m"])}" fill="var(--intl)" stroke="var(--intl)" stroke-width="2"/>')
sb = 400 * 1000 * k
scalebar = (f'<g font-size="11" fill="var(--ink-2)"><rect x="12" y="{H - 16}" width="{sb:.1f}" height="4" fill="var(--ink-2)"/>'
            f'<text x="{12 + sb + 6:.1f}" y="{H - 11}">400 km</text></g>')


def svgmap(inner, label):
    return f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{e(label)}">{base}{inner}{scalebar}</svg>'


def kcol(p):
    return "var(--accent)" if p >= 98 else "var(--kmid)" if p >= 50 else "var(--gap)" if p > 0 else "var(--kzero)"


kpaths = "".join(f'<path d="{path(kk["geom"])}" fill="{kcol(kk["pct"])}" fill-opacity="0.9" stroke="var(--ink)" stroke-width="0.4">'
                 f'<title>{e(kk["name"])}: {kk["pct"]:.1f}% covered</title></path>' for kk in sorted(kgeo["kba"], key=lambda kk: -kk["pct"]))
ghost = (f'<path d="{path(simp(geo["pa_t"], 1500))}" fill="none" stroke="var(--ink-2)" stroke-width="0.5" stroke-dasharray="2 2"/>'
         f'<path d="{path(simp(geo["oe_t"], 2500))}" fill="none" stroke="var(--oecm)" stroke-width="0.5" stroke-dasharray="2 2"/>')
legend = ('<ul class="legend"><li><i style="background:var(--nat)"></i>National PA</li><li><i style="background:var(--intl)"></i>International PA '
          '(Ramsar, World Heritage)</li><li><i style="background:var(--reg)"></i>Regional PA (SPAMI)</li><li><i style="background:var(--oecm)"></i>OECM (Cultural Park)</li></ul>')
legend2 = ('<ul class="legend"><li><i style="background:var(--accent)"></i>Protected areas</li><li><i style="background:var(--oecm)"></i>OECMs, PA area removed</li>'
           '<li><i style="background:var(--intl)"></i>Marine PAs</li><li><i style="background:var(--sea);border:1px solid var(--sea-line)"></i>EEZ</li></ul>')
klegend = ('<ul class="legend"><li><i style="background:var(--accent)"></i>Complete (≥ 98%)</li><li><i style="background:var(--kmid)"></i>50–98%</li>'
           '<li><i style="background:var(--gap)"></i>Under 50%</li><li><i style="background:var(--kzero)"></i>Not covered</li>'
           '<li><i style="border:1px dashed var(--oecm);background:none"></i>PA / OECM outlines</li></ul>')


# ------------------------------------------------------------------ sheet mocks
def mock(sheet, cols, rows, note=None):
    h = [f'<figure class="sheet"><figcaption><span class="tab">{e(sheet)}</span>{e(note) if note else ""}</figcaption><div class="scroll"><table class="grid">',
         '<thead><tr><th class="rn"></th>' + "".join(f"<th>{c}</th>" for c, _ in cols) + "</tr>"]
    if any(hd for _, hd in cols):
        h.append('<tr class="hdr"><td class="rn"></td>' + "".join(f"<td>{e(hd)}</td>" for _, hd in cols) + "</tr>")
    h.append("</thead><tbody>")
    for rn, cells in rows:
        h.append(f'<tr><td class="rn">{rn}</td>' + "".join(f'<td class="{kk}">{e(str(v))}</td>' for v, kk in cells) + "</tr>")
    h.append("</tbody></table></div></figure>")
    return "".join(h)


def f2(x, d=2):
    return "" if x in ("", None) else (f"{x:,.{d}f}" if isinstance(x, float) else str(x))


setup_rows = [(4, "Country / jurisdiction", "Algeria"), (5, "ISO3 code", "DZA"), (6, "Reporting year", "2026"),
              (7, "WDPA / WD-OECM release used", "WDPA/WD-OECM October 2026"), (8, "KBA dataset version", "World Database of KBAs, September 2026"),
              (9, "Base map used", "geoBoundaries ADM0 + Marine Regions EEZ v12, Mollweide"), (10, "Terrestrial area (km²)", "2,318,644.15"),
              (11, "Marine & coastal area (km²)", "131,439.54"), (12, "Target coverage", "30.0%"), (14, "PA layer flattened in GIS?", "Y"),
              (15, "OECM layer: PA overlap erased?", "Y"), (16, "Mollweide equal-area?", "Y"), (17, "Overlaps attributed to earliest site?", "Y"),
              (26, "PAME validity window (years)", "5"), (27, "Time-series start year", "1940")]
setup_mock = mock("Setup", [("A", "Parameter"), ("B", "Value")], [(r, [(l, "lab"), (v, "in")]) for r, l, v in setup_rows], " rows 4–27 (selection)")

sel = [12352, 4999, 20389, 23177, 555705342, 555705343, 555705341, 9741, 17706, 900580, 72354, 19571, 555599909, 555698157, 555698159]
rowno = {r: 5 + i for i, r in enumerate(reg)}
reg_rows = []
for sid in sel:
    r = reg[sid]
    excl = "UNESCO-MAB Biosphere Reserve" if r[15] == "Y" else ""
    reg_rows.append((rowno[sid], [(r[0], "in"), (r[1], "in"), (r[2], "in"), (r[4], "in"), (r[7], "in"), (r[8], "in"), (r[10], "in"),
                                  (f2(r[11], 0), "in"), (f2(r[17], 1), "in"), (f2(r[18], 2), "in"), (r[21], "in"),
                                  (0 if excl else 1, "warn" if excl else "calc"), (excl, "warn" if excl else "calc")]))
reg_mock = mock("PA_OECM_Register", [("A", "SITE_ID"), ("B", "NAME"), ("C", "DESIG_ENG"), ("E", "Type"), ("H", "STATUS"), ("I", "STATUS_YR"),
                                     ("K", "Geometry"), ("L", "REP_AREA"), ("R", "NET terr. km²"), ("S", "NET marine km²"), ("V", "PAME yr"),
                                     ("Z", "Included"), ("AA", "Exclusion reason")], reg_rows, " 15 of the 78 real rows, chosen to show each rule")

head_mock = mock("Headline_3.1", [("A", "Realm"), ("B", "Realm km²"), ("E", "PA used"), ("F", "OECM used"), ("H", "PA %"), ("I", "OECM %"),
                                  ("J", "Indicator 3.1"), ("L", "Gap (pp)"), ("M", "Extra km²"), ("N", "Status")],
                 [(6, [("Terrestrial & inland waters", "lab"), ("2,318,644.15", "calc"), ("107,763.96", "calc"), ("1,151,696.35", "calc"),
                       ("4.65%", "calc"), ("49.67%", "calc"), ("54.32%", "key"), ("0.0", "calc"), ("0.00", "calc"), ("Target met", "pass")]),
                  (7, [("Marine & coastal", "lab"), ("131,439.54", "calc"), ("89.78", "calc"), ("0.00", "calc"), ("0.07%", "calc"), ("0.00%", "calc"),
                       ("0.07%", "key"), ("29.9", "calc"), ("39,342.08", "calc"), ("Below target", "warn")])], " section A")

eco = list(csv.DictReader(open(f"{OUTD}/ecoregion_coverage.csv")))
meow = list(csv.DictReader(open(f"{OUTD}/marine_ecoregion_coverage.csv")))
eco_rows = []
for i, u in enumerate(sorted(eco, key=lambda x: -float(x["extent_km2"])) + meow):
    ext, p, o = float(u["extent_km2"]), float(u["pa_km2"]), float(u["oecm_km2"])
    pct = (p + o) / ext
    eco_rows.append((58 + i, [(u.get("eco_name") or u["ecoregion"], "in"), (f2(ext, 0), "in"), (f2(p, 0), "in"), (f2(o, 0), "in"),
                              (f"{pct:.1%}", "key"), ("Yes" if pct >= 0.3 else "No", "pass" if pct >= 0.3 else "warn")]))
eco_mock = mock("Ecosystems", [("C", "Ecoregion"), ("F", "Extent km²"), ("G", "PA km²"), ("H", "OECM km²"), ("J", "Coverage"), ("K", "≥ 30%?")],
                eco_rows, " section D: 10 terrestrial and 2 marine ecoregions")
biome_mock = mock("Ecosystems", [("A", "GET"), ("C", "Biome / component"), ("F", "Extent"), ("G", "PA"), ("H", "OECM"), ("J", "Coverage")],
                  [(7, [("T2", "lab"), ("Temperate-boreal forests and woodlands", "lab"), ("9,442", "in"), ("807", "in"), ("0", "in"), ("8.5%", "key")]),
                   (8, [("T3", "lab"), ("Shrublands and shrub-dominated woodlands", "lab"), ("292,985", "in"), ("20,124", "in"), ("84,892", "in"), ("35.8%", "key")]),
                   (9, [("T4", "lab"), ("Savannas and grasslands", "lab"), ("33,435", "in"), ("0", "in"), ("33,429", "in"), ("100.0%", "key")]),
                   (10, [("T5", "lab"), ("Deserts and semi-deserts", "lab"), ("1,982,742", "in"), ("86,831", "in"), ("1,033,375", "in"), ("56.5%", "key")]),
                   (52, [("Rivers", "lab"), ("Rivers and streams (HydroRIVERS, km)", "lab"), ("572,882", "in"), ("27,185", "in"), ("277,793", "in"), ("53.2%", "key")]),
                   (53, [("Wetlands", "lab"), ("Lakes and wetlands (GLWD v2, km²)", "lab"), ("28,321", "in"), ("9,501", "in"), ("4,142", "in"), ("48.2%", "key")])],
                  " sections A and C")
wg = [x for x in csv.DictReader(open(f"{OUTD}/glwd_wetland_coverage_by_group.csv")) if x["counted"] == "Y"]
wet_mock = mock("GLWD v2 · outputs/glwd_wetland_coverage_by_group.csv", [("", "Wetland group"), ("", "Extent km²"), ("", "PA km²"), ("", "OECM km²"), ("", "PA + OECM")],
                [(i + 1, [(x["group"], "lab"), (f2(float(x["extent_km2"]), 0), "calc"), (f2(float(x["pa_km2"]), 0), "calc"),
                          (f2(float(x["oecm_km2"]), 0), "calc"), (f'{float(x["pa_oecm_pct"]):.1f}%', "key")]) for i, x in enumerate(wg)]
                + [("Σ", [("Lakes and wetlands → Ecosystems row 53", "lab"), ("28,321", "calc"), ("9,501", "calc"), ("4,142", "calc"), ("48.2%", "key")])],
                " GIS output")

kba_by = {r[0]: r for r in cfg["kba"]}
krow = {r[0]: 16 + i for i, r in enumerate(cfg["kba"])}
kba_rows = []
for sid in [6184, 6183, 46581, 6181, 31707, 46577, 46579, 31751, 31674, 6157, 6185, 46578]:
    r = kba_by[sid]
    pa_p, all_p = min(1, r[7] / r[2]), min(1, (r[7] + r[8]) / r[2])
    cls = "Complete" if all_p >= 0.98 else ("Partial" if all_p > 0 else "None")
    kba_rows.append((krow[sid], [(r[0], "in"), (r[1], "in"), (f2(r[2], 1), "in"), (f2(r[3], 2), "in"), (r[5], "in"), (r[6], "in"),
                                 (f2(r[7], 1), "in"), (f2(r[8], 1), "in"), (f"{all_p:.1%}", "key"), (f"{pa_p:.1%}", "calc"),
                                 (cls, "pass" if cls == "Complete" else ("warn" if cls == "None" else "calc"))]))
kba_mock = mock("KBA_Coverage", [("A", "SitRecID"), ("B", "KBA name"), ("C", "Area km²"), ("D", "Ocean frac."), ("F", "Freshw."), ("G", "Mountain"),
                                 ("H", "PA km²"), ("I", "OECM km²"), ("L", "% PA+OECM"), ("M", "% PA only"), ("O", "Class")],
                kba_rows, " 12 of 65 rows, all values from the KBA polygons")
kba_sum = mock("KBA_Coverage", [("A", "KBA group"), ("B", "SDG"), ("C", "KBAs"), ("D", "Mean % PA+OECM"), ("E", "Mean % PA only"), ("G", "None"),
                                ("H", "Partial"), ("I", "Complete")],
               [(6, [("All KBAs", "lab"), ("—", "calc"), ("65", "calc"), ("43.5%", "key"), ("35.1%", "calc"), ("26", "calc"), ("22", "calc"), ("17", "calc")]),
                (7, [("Terrestrial KBAs", "lab"), ("15.1.2", "calc"), ("63", "calc"), ("42.9%", "key"), ("34.3%", "calc"), ("26", "calc"), ("21", "calc"), ("16", "calc")]),
                (8, [("Freshwater KBAs", "lab"), ("15.1.2", "calc"), ("24", "calc"), ("60.2%", "key"), ("60.2%", "calc"), ("4", "calc"), ("11", "calc"), ("9", "calc")]),
                (9, [("Marine KBAs (≥5% ocean)", "lab"), ("14.5.1", "calc"), ("4", "calc"), ("43.9%", "key"), ("43.9%", "calc"), ("1", "calc"), ("2", "calc"), ("1", "calc")]),
                (10, [("Mountain KBAs", "lab"), ("15.4.1", "calc"), ("42", "calc"), ("22.7%", "key"), ("16.0%", "calc"), ("24", "calc"), ("15", "calc"), ("3", "calc")])],
               " section A (results)")

gov_mock = mock("Governance", [("A", "IUCN governance type"), ("B", "Sites"), ("C", "Terr. PA km²"), ("D", "Terr. OECM km²"), ("G", "% of covered land")],
                [(6, [("A. Governance by government", "lab"), ("68", "calc"), ("31,900.57", "calc"), ("1,151,696.35", "calc"), ("94.0%", "key")]),
                 (7, [("B. Shared governance", "lab"), ("0", "calc"), ("0", "calc"), ("0", "calc"), ("0.0%", "calc")]),
                 (8, [("C. Private governance", "lab"), ("0", "calc"), ("0", "calc"), ("0", "calc"), ("0.0%", "calc")]),
                 (9, [("D. Indigenous peoples & local communities", "lab"), ("0", "calc"), ("0", "calc"), ("0", "calc"), ("0.0%", "calc")]),
                 (10, [("Not reported", "lab"), ("2", "calc"), ("75,863.39", "warn"), ("0", "calc"), ("6.0%", "warn")]),
                 (11, [("TOTAL", "lab"), ("70", "calc"), ("107,763.96", "calc"), ("1,151,696.35", "calc"), ("100%", "calc")])], " section A")

pame_mock = mock("Mgmt_Effectiveness", [("A", "Effectiveness class"), ("B", "Sites"), ("C", "Terr. PA km²"), ("D", "Terr. OECM km²"), ("G", "% of covered land")],
                 [(6, [("High / Moderate / Low (scored)", "lab"), ("0", "calc"), ("0", "calc"), ("0", "calc"), ("0.0%", "calc")]),
                  (9, [("Assessed – no score (Tassili, 2025)", "lab"), ("1", "calc"), ("75,619.42", "key"), ("0", "calc"), ("6.0%", "key")]),
                  (10, [("Assessment outdated (2001–2014)", "lab"), ("13", "calc"), ("1,550.24", "warn"), ("1,151,696.35", "warn"), ("91.6%", "warn")]),
                  (11, [("Not assessed", "lab"), ("56", "calc"), ("30,594.30", "calc"), ("0", "calc"), ("2.4%", "calc")])], " section A (selection)")

qc = [("Realm areas entered", "Both", "PASS"), ("PA layer flattened", "Y", "PASS"), ("OECMs: PA overlap erased", "Y", "PASS"),
      ("Mollweide projection", "Y", "PASS"), ("Included sites without flattened net area", "0", "PASS"), ("Terrestrial coverage ≤ 100%", "54.32%", "PASS"),
      ("Marine coverage ≤ 100%", "0.07%", "PASS"), ("Included sites with any QC flag", "12", "WARN"), ("Included sites with STATUS_YR missing", "0", "PASS"),
      ("Included point (buffered) sites", "2", "INFO"), ("Share of area with GOV_TYPE not reported", "6.0%", "WARN"),
      ("Governance total = headline total", "0.000", "PASS"), ("KBAs with covered area > KBA area", "0", "PASS")]
qc_mock = mock("QC_Checks", [("B", "Check"), ("C", "Value"), ("D", "Result")], [(5 + i, [(a, "lab"), (b, "calc"), (c, c.lower())]) for i, (a, b, c) in enumerate(qc)],
               " selection of the 20 checks")


# ------------------------------------------------------------------ charts
def gauge(segs, label, note):
    w, h, pad = 560, 92, 16
    sx = lambda x: pad + x / 60 * (w - 2 * pad)
    ticks = "".join(f'<line x1="{sx(t):.1f}" x2="{sx(t):.1f}" y1="52" y2="58" stroke="var(--ink-2)"/><text x="{sx(t):.1f}" y="72" text-anchor="middle">{t}%</text>' for t in range(0, 61, 10))
    x0, bars = 0, ""
    for v, col in segs:
        bars += f'<rect x="{sx(x0):.1f}" y="20" width="{max(1.5, sx(x0 + v) - sx(x0)):.1f}" height="30" fill="{col}"/>'
        x0 += v
    return f'''<svg viewBox="0 0 {w} {h}" role="img" aria-label="{e(label)} coverage {x0:.2f} percent against 30 percent target" class="chart">
<rect x="{pad}" y="20" width="{w - 2 * pad}" height="30" rx="3" fill="var(--track)"/>{bars}
<line x1="{sx(30):.1f}" x2="{sx(30):.1f}" y1="12" y2="56" stroke="var(--ink)" stroke-width="2"/>
<text x="{sx(30) + 6:.1f}" y="14" class="lab">Target 30%</text><text x="{pad + 4}" y="14" class="lab">{e(label)}</text>
<text x="{min(sx(x0) + 6, w - 60):.1f}" y="40" class="val">{x0:.2f}%</text>{ticks}
<text x="{w / 2:.1f}" y="88" text-anchor="middle" class="lab">{e(note)}</text></svg>'''


def bars():
    w, h = 560, 150
    rows = [("PAs: sum of site areas", 108450, "var(--gap)"), ("PAs: after flattening", 107764, "var(--accent)"),
            ("OECMs: sum of site areas", 1233094, "var(--gap)"), ("OECMs: PA area removed", 1151696, "var(--oecm)")]
    sx = lambda v: 210 + v / 1300000 * (w - 300)
    out = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Gross versus flattened area for PAs and OECMs" class="chart">']
    for i, (lab, v, c) in enumerate(rows):
        y = 6 + i * 36
        out.append(f'<text x="200" y="{y + 17}" text-anchor="end" class="lab">{lab}</text><rect x="210" y="{y}" width="{max(2, sx(v) - 210):.1f}" height="24" rx="2" fill="{c}"/>'
                   f'<text x="{sx(v) + 6:.1f}" y="{y + 17}" class="val">{v:,.0f} km²</text>')
    return "".join(out) + "</svg>"


def tschart():
    w, h, l, r, t, b = 560, 250, 44, 16, 16, 30
    sx = lambda y: l + (y - 1940) / (2030 - 1940) * (w - l - r)
    sy = lambda v: t + (1 - v / 60) * (h - t - b)
    grid = "".join(f'<line x1="{l}" x2="{w - r}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" stroke="var(--line)"/><text x="{l - 6}" y="{sy(v) + 4:.1f}" text-anchor="end">{v}%</text>' for v in (0, 10, 20, 30, 40, 50, 60))
    xt = "".join(f'<text x="{sx(y):.1f}" y="{h - 10}" text-anchor="middle">{y}</text>' for y in (1940, 1960, 1980, 2000, 2020))

    def step(idx):
        pts = []
        for i, row in enumerate(ts):
            if i:
                pts.append(f"{sx(row[0]):.1f},{sy(ts[i - 1][idx]):.1f}")
            pts.append(f"{sx(row[0]):.1f},{sy(row[idx]):.1f}")
        return " ".join(pts)
    return f'''<svg viewBox="0 0 {w} {h}" role="img" aria-label="Coverage over time 1940 to 2026" class="chart">{grid}{xt}
<line x1="{l}" x2="{w - r}" y1="{sy(30):.1f}" y2="{sy(30):.1f}" stroke="var(--ink)" stroke-dasharray="5 4"/><text x="{l + 4}" y="{sy(30) - 6:.1f}" class="lab">30% by 2030</text>
<polygon points="{sx(1940):.1f},{sy(0):.1f} {step(1)} {sx(2026):.1f},{sy(0):.1f}" fill="var(--oecm)" fill-opacity="0.18"/>
<polyline points="{step(1)}" fill="none" stroke="var(--oecm)" stroke-width="2.5"/>
<polyline points="{step(2)}" fill="none" stroke="var(--accent)" stroke-width="2.5"/>
<polyline points="{step(3)}" fill="none" stroke="var(--intl)" stroke-width="2"/>
<text x="{sx(2026) - 6:.1f}" y="{sy(54.32) - 8:.1f}" text-anchor="end" class="val" style="fill:var(--oecm)">land, PA+OECM 54.3%</text>
<text x="{sx(2026) - 6:.1f}" y="{sy(4.65) - 8:.1f}" text-anchor="end" class="val" style="fill:var(--accent)">land, PA only 4.65%</text>
<text x="{sx(2026) - 6:.1f}" y="{sy(0.07) + 14:.1f}" text-anchor="end" class="val" style="fill:var(--intl)">sea 0.07%</text>
<text x="{sx(1987) - 4:.1f}" y="{sy(29.46) - 8:.1f}" text-anchor="end" class="lab">1987: Ahaggar</text>
<text x="{sx(2008) - 4:.1f}" y="{sy(54.3) - 8:.1f}" text-anchor="end" class="lab">2008: Tindouf, Touat, Atlas Saharien</text></svg>'''


steps = [("data", "Collect the data"), ("setup", "Fill in Setup"), ("gis", "Flatten PAs and OECMs in GIS"), ("register", "Enter the site register"),
         ("headline", "Read the headline"), ("oecm", "The OECM question"), ("eco", "Ecosystems and inland waters"), ("kba", "Key Biodiversity Areas"),
         ("gov", "Governance"), ("pame", "Management effectiveness"), ("ts", "Time series"), ("qc", "Quality checks and reconciliation"),
         ("report", "Report"), ("gaps", "What this example leaves out")]
nav = "".join(f'<li><a href="#{a}"><span>{i + 1:02d}</span>{e(t)}</a></li>' for i, (a, t) in enumerate(steps))


def head(i, title, sheet=None):
    chip = f'<span class="chip">{e(sheet)}</span>' if sheet else ""
    return f'<section class="step" id="{steps[i][0]}"><div class="stephead"><span class="num">STEP {i + 1:02d}</span>{chip}</div><h2>{e(title)}</h2>'


cellkey = ('<div class="cellkey"><span><i style="background:var(--in-bg)"></i>Input you type or paste</span><span><i style="background:var(--calc-bg)"></i>Formula, computed by the tool</span>'
           '<span><i style="background:var(--key-bg)"></i>Key result</span><span><i style="background:var(--warn-bg)"></i>Flag to act on</span></div>')

body = f"""
<div class="wrap">
<nav class="index" aria-label="Steps"><p class="lbl">Walkthrough</p><ol>{nav}</ol></nav>
<main>
<header class="hero">
<div class="eyebrow">GBF Headline Indicator 3.1 · National worked example with real data</div>
<h1>Algeria, step by step through the 30×30 tool</h1>
<p class="lede">This guide fills the Indicator 3.1 Excel tool for Algeria from the 78 records in the October 2026 World Database on Protected Areas and World Database on OECMs, the 65 official Key Biodiversity Area polygons (September 2026), and a GIS run over land and sea. Every number comes from those data and from the workbook recalculated in Excel.</p>
<p>Algeria is a case where the OECM column decides the answer. Its protected areas cover under 5% of the land. Its five Saharan Cultural Parks, reported to the WD-OECM, cover almost half of it. Together they put the land figure far above 30%, while the sea stays below 0.1%.</p>
<div class="facts six">
<div><b>78</b><small>records: 71 PA polygons, 2 PA points, 5 OECMs</small></div>
<div><b>4.65%</b><small>of land in protected areas</small></div>
<div><b>49.67%</b><small>of land added by OECMs</small></div>
<div><b>54.32%</b><small>land coverage, PAs + OECMs (target met)</small></div>
<div><b>0.07%</b><small>of 131,440 km² of sea</small></div>
<div><b>39,342 km²</b><small>of sea still needed for 30%</small></div>
</div>
</header>

{head(0, "Collect the data")}
<p>Everything used here is in the <code>algeria/01_data</code> folder, with the source of each file:</p>
<ol class="do">
<li><b>Protected areas and OECMs.</b> WDPA and WD-OECM, October 2026, from the UNEP-WCMC map service behind <a href="https://www.protectedplanet.net/country/DZA">Protected Planet</a>: 71 protected-area polygons, 2 points and 5 OECM polygons, as shapefile, GeoJSON and GeoPackage.</li>
<li><b>Base map.</b> Land: the geoBoundaries ADM0 outline. Sea: the Marine Regions EEZ v12, Algeria's 200-nautical-mile zone, with coastal gaps closed (47 km²). Both projected to Mollweide.</li>
<li><b>Key Biodiversity Areas.</b> The World Database of KBAs, September 2026: 65 Algerian polygons and 2 points, plus 213 trigger-species records. The KBA data are licensed; don't republish the polygons.</li>
<li><b>Management effectiveness.</b> GD-PAME evaluations listed on the 78 site pages on Protected Planet: 16 sites carry at least one.</li>
<li><b>Ecosystems, mountains and inland waters.</b> RESOLVE Ecoregions 2017, Marine Ecoregions of the World, the GMBA Mountain Inventory v2.0, HydroRIVERS v1.0 and GLWD v2, clipped to Algeria by <code>00_prepare_layers.py</code>.</li>
</ol>

{head(1, "Fill in Setup", "Sheet: Setup")}
<p>Setup holds the two denominators and the method declarations. Row 15 matters here for the first time: Algeria has OECMs, so you must confirm that every OECM has had its protected-area overlap erased before it is measured.</p>
{setup_mock}
{cellkey}

{head(2, "Flatten PAs and OECMs in GIS", "Outside Excel: 03_analysis/scripts/01_gis_flatten.py")}
<p>The metadata treats the two layers differently. Protected areas are dissolved into one flat layer. OECMs are then measured only where no protected area lies, so the same ground is never counted twice, and never as an OECM when it is already protected.</p>
<div class="maps">
<figure><figcaption><b>Before: 70 records</b>Stacked records over the same ground</figcaption>{svgmap(before, "Protected-area and OECM records in Algeria")}{legend}</figure>
<figure><figcaption><b>After: PAs, then OECMs</b>107,764 km² of PAs and 1,151,696 km² of OECMs, each counted once</figcaption>{svgmap(flat, "Flattened PA and OECM layers in Algeria")}{legend2}</figure>
</div>
{bars()}
<h3>The procedure (metadata steps 1–6)</h3>
<ol class="do">
<li><b>Filter.</b> All eight UNESCO biosphere reserves drop out (Tassili, El Kala, Djurdjura, Chréa, Taza, Gouraya, Belezma, Tlemcen). Their core zones are counted through the national parks and the World Heritage site.</li>
<li><b>Buffer points.</b> Two designated points become circles: Djebel Aïssa National Park (244 km²) and the Habibas islands marine reserve (27 km², all at sea).</li>
<li><b>Clip and project.</b> Each site is split into land and sea parts and measured in Mollweide.</li>
<li><b>Dissolve PAs.</b> 108,450 km² summed becomes <b>107,764 km²</b> on land; at sea, 107 km² becomes <b>89.8 km²</b>.</li>
<li><b>Erase PAs from OECMs, then dissolve.</b> The Cultural Parks sum to 1,233,094 km². Removing the protected areas inside them, above all the 75,470 km² of the Tassili n'Ajjer World Heritage Site inside the Tassili Cultural Park, leaves <b>1,151,696 km²</b>.</li>
<li><b>Attribute overlaps.</b> Protected areas first, then OECMs; within each, the earliest designation keeps the overlap. Three Ramsar records lose all their area: Lac Oubeïra (inside El Kala National Park), Vallée d'Iherir (inside the Tassili World Heritage site) and Tourbière du Lac Noir.</li>
</ol>

{head(3, "Enter the site register", "Sheet: PA_OECM_Register")}
<p>All 78 records go in. Column E says whether each is a protected area or an OECM; the tool keeps the two apart in every table. Paste the attributes into the yellow columns and the net land and sea areas into R and S.</p>
{reg_mock}
<p>The Tassili Cultural Park keeps 63,128 of its 138,579 km² as OECM, because the World Heritage site inside it is counted as a protected area. The two Habibas records show the point rule at sea: the 2003 reserve circle holds 26.8 km², the 2005 SPAMI polygon only the 9.2 km² outside it.</p>

{head(4, "Read the headline", "Sheet: Headline_3.1")}
{head_mock}
{gauge([(4.6477, "var(--accent)"), (49.6711, "var(--oecm)")], "Land", "protected areas 4.65% + OECMs 49.67% = 54.32%")}
{gauge([(0.0683, "var(--intl)")], "Sea", "gap 29.9 points = 39,342 km²")}
<div class="result"><div><strong>Result.</strong> PAs and OECMs cover <b>54.32%</b> of Algeria's land, so the land element of Target 3 is met. They cover <b>0.07%</b> of its waters: 90 km² out of 131,440 km². Reaching 30% at sea would take another <b>39,342 km²</b>; even the national target of 5% needs another 6,482 km².</div></div>

{head(5, "The OECM question")}
<p>The land result rests on one decision: whether the five Cultural Parks are OECMs. Algeria has reported them to the WD-OECM, and Protected Planet counts them, so the indicator does too. Without them, coverage would be 4.65%.</p>
<div class="pitfall"><h3>What to check before reporting</h3>
<p>An OECM must meet the criteria in CBD decision 14/8: a defined area, governed and managed in ways that achieve positive, long-term outcomes for biodiversity, whatever its primary purpose. The Cultural Parks protect cultural and natural heritage together and cover mostly desert. Your report should state the basis for their OECM status, and the management-effectiveness step below shows how thin the evidence on their outcomes is: one METT assessment each, from 2011.</p>
<p>Report the PA and OECM figures side by side, as the tool does (4.65% and 49.67%), rather than the total alone.</p></div>

{head(6, "Ecosystems and inland waters", "Sheet: Ecosystems")}
<p>The flat layers were intersected with Algeria's ten terrestrial ecoregions and two marine ecoregions. Coverage is very uneven.</p>
{eco_mock}
<p>The ecoregions are grouped into Global Ecosystem Typology biomes using the crosswalk in <code>country.json</code>. Rivers come from HydroRIVERS, and lakes and wetlands from GLWD v2 (script <code>03_wetlands_glwd.py</code>), counting river channels by length only and leaving out rice paddies.</p>
{biome_mock}
{wet_mock}
<div class="result"><div><strong>Finding.</strong> The Sahara is well covered, almost entirely through OECMs; the Mediterranean north is not. Mediterranean woodlands and forests (135,146 km²) are 13.3% covered and Mediterranean conifer forests 8.5%, with no OECM contribution. Salt pans and chotts are 85% covered, but marshes only 15% and riverine wetlands 20%. The river figure of 53% is mostly dry Saharan wadis inside the Cultural Parks. At sea, both marine ecoregions are under 0.4%.</div></div>

{head(7, "Key Biodiversity Areas", "Sheet: KBA_Coverage · script 02_kba_overlay.py")}
<p>Each of the 65 KBA polygons is overlaid with the flat PA layer and the PA-erased OECM layer, so the sheet shows both sources of coverage. Two KBAs (Béni Abbès, Garaet Haouas) exist only as points with no area and cannot be measured.</p>
<div class="maps one"><figure><figcaption><b>65 KBAs by share covered (PAs + OECMs)</b>Official KBA polygons, September 2026</figcaption>{svgmap(ghost + kpaths, "Key Biodiversity Areas of Algeria coloured by covered share")}{klegend}</figure></div>
{kba_mock}
{kba_sum}
<p>Realm rules, as for any country: a KBA is marine with at least 5% of its area outside the land, mountain with at least 5% inside the GMBA mountain inventory, and freshwater if its factsheet, name or trigger species point to fresh water.</p>
<div class="result"><div><strong>Finding.</strong> On average, Algerian KBAs are <b>43.5%</b> covered, 35.1% by protected areas alone. Seventeen are fully covered, mostly Saharan sites and wetlands. Mountain KBAs are the gap: 42 KBAs, average 22.7%, and 24 with no coverage at all. The largest unprotected areas are all in the northern mountains: Aurès–Chélia (4,845 km²), the Dahra range (3,415 km²), Monts des Traras (1,687 km²), Haut Seybouse and the Bibans.</div></div>
<p>The PA-only results match the KBA database's own coverage figures for every KBA, which confirms the protected-area layer. The difference is the OECMs, which the KBA database doesn't count: Ahaggar rises from 0.8% to 100%, Djebel Amour from 0% to 100%. One Moroccan KBA (Jbel Krouz) overlaps Algerian land by 85 km² along the border; it is listed in <code>kba_foreign_overlapping_DZA.csv</code> and not counted.</p>

{head(8, "Governance", "Sheet: Governance")}
{gov_mock}
<div class="result"><div><strong>Finding.</strong> Every reported site is governed by a national ministry, apart from two with no governance type: the Tassili n'Ajjer World Heritage site and Djebel Aïssa National Park. Because Tassili is so large, they make up 6.0% of the covered area, above the 5% QC threshold, so the check raises a warning. A WDPA update for Tassili would clear it.</div></div>

{head(9, "Management effectiveness", "Sheet: Mgmt_Effectiveness")}
<p>Sixteen site pages list GD-PAME evaluations: METT assessments of national parks (2013, 2014) and of the four larger Cultural Parks (2011), BREMi evaluations of the biosphere reserves (2013), BirdLife IBA monitoring (2001) and World Heritage Outlooks for Tassili n'Ajjer up to 2025.</p>
<div class="pitfall"><h3>Evaluations on excluded records</h3>
<p>Six BREMi evaluations sit on biosphere-reserve records, which the method excludes. They were moved to the national park or World Heritage record covering the same site (Tassili, Chréa, El Kala, Taza, Gouraya, Djurdjura), as listed in <code>country.json</code>. Column Y records each move.</p></div>
{pame_mock}
<p>Only Tassili has an evaluation from the last five years, and none has a numeric score. The Cultural Parks, 91% of the covered land, were last assessed in 2011. Report this breakdown as provisional.</p>

{head(10, "Time series", "Sheet: Time_Series")}
{tschart()}
<p>Almost all of today's land coverage comes from three moments: Ahaggar in 1987, and Tindouf, Touat-Gourara-Tidikelt and Atlas Saharien in 2008. Protected areas alone have grown slowly, from 3.3% in 1983 to 4.65%, mainly through the 2001–2004 Ramsar listings. At sea, the Cap Lindles reserve (2019) doubled a very small figure.</p>
<p>One limit of the net-area method: because protected areas take precedence, the part of the Tassili Cultural Park that overlaps the 1982 World Heritage site is dated 1982, not 1972. The curve therefore understates coverage between 1972 and 1982.</p>

{head(11, "Quality checks and reconciliation", "Sheet: QC_Checks")}
{qc_mock}
<p>Two warnings: 12 flagged sites, mostly realm mismatches between the WDPA field and the GIS split (coastal parks such as El Kala, Taza and Gouraya with small sea parts), and the governance gap above.</p>
<div class="scroll"><table class="recon"><thead><tr><th></th><th>PA land</th><th>PA + OECM land</th><th>Sea</th></tr></thead><tbody>
<tr><td>This workbook (geoBoundaries + Marine Regions EEZ)</td><td>107,764 of 2,318,644 km² = 4.65%</td><td>1,259,460 km² = 54.32%</td><td>90 of 131,440 km² = 0.07%</td></tr>
<tr><td>Protected Planet, October 2026</td><td>107,456 of 2,307,910 km² = 4.66%</td><td>1,255,842 km² = 54.41%</td><td>92 of 131,247 km² = 0.07%</td></tr>
<tr><td>Algeria's 7th National Report (2026)</td><td>10 forest national parks, 8,550 km²</td><td>Cultural Parks alone: 1,042,557 km² = 43.77% of the territory</td><td>–</td></tr>
<tr><td>National targets (NBSAP, 6th National Report)</td><td colspan="2">50% of land by 2030</td><td>5% of sea by 2030</td></tr>
</tbody></table></div>
<p>The workbook and Protected Planet agree within 0.1 points. The national report uses the legal areas of the Cultural Parks and the official national territory (2,381,741 km²), so its 43.77% is not directly comparable: the WDPA outlines of the parks are larger (1,233,094 km² before overlaps are removed). Explain this in the report rather than mixing the two sources. The planned Saoura Cultural Park (92,014 km²) would add about 4 points once it is designated and reported.</p>

{head(12, "Report", "Sheet: Dashboard")}
<blockquote class="draft">In 2026, protected areas covered 107,764 km², or 4.65% of Algeria's terrestrial and inland water area, and other effective area-based conservation measures (the five Cultural Parks) a further 1,151,696 km², or 49.67%; together 54.32% (Headline Indicator 3.1; WDPA/WD-OECM October 2026; Mollweide equal-area). Marine and coastal coverage was 90 km², or 0.07%; reaching 30% would require a further 39,342 km², and the national 5% target a further 6,482 km². On average, Algeria's 65 Key Biodiversity Areas are 43.5% covered (mountain KBAs 22.7%). Coverage ranges from 8.5% of Mediterranean conifer forests to over 99% of Saharan montane woodlands. All reported sites are government-governed; 6% of the covered area has a current but unscored effectiveness evaluation.</blockquote>

{head(13, "What this example leaves out")}
<ol class="do">
<li><b>The OECM evidence.</b> The tool counts the Cultural Parks as reported. Checking each against the CBD 14/8 criteria is a national task, not a GIS step.</li>
<li><b>Marine biomes.</b> Splitting the sea into shelf and pelagic waters needs bathymetry.</li>
<li><b>Effectiveness scores.</b> GD-PAME gives the method and year, not the score.</li>
<li><b>Sites not yet in the WDPA.</b> Recent national parks and the planned Saoura Cultural Park are missing until reported to UNEP-WCMC.</li>
</ol>

<h3>Sources</h3>
<ul class="sources">
<li>UNEP-WCMC &amp; IUCN (2026). <a href="https://www.protectedplanet.net/country/DZA">Protected Planet: Algeria</a>, WDPA/WD-OECM October 2026, and GD-PAME records on each site page.</li>
<li>GBF Indicators. <a href="https://www.gbf-indicators.org/metadata/headline/3-1">Metadata for Headline Indicator 3.1</a>. CBD decision 14/8 on OECMs.</li>
<li>BirdLife International on behalf of the KBA Partnership (2026). World Database of Key Biodiversity Areas, September 2026, and KBA trigger species.</li>
<li>République Algérienne Démocratique et Populaire (2026). 7th National Report to the CBD; 6th National Report; Stratégie et Plan d'Action Nationaux pour la Biodiversité.</li>
<li>Flanders Marine Institute (2023). EEZ v12. Runfola, D. et al. (2020). geoBoundaries. Snethlage, M.A. et al. (2022). GMBA Mountain Inventory v2.</li>
<li>Dinerstein, E. et al. (2017). BioScience 67(6): 534–545. Spalding, M.D. et al. (2007). BioScience 57(7): 573–583. Lehner, B. &amp; Grill, G. (2013). HydroRIVERS. Lehner, B. et al. (2025). GLWD v2. ESSD 17: 2277–2329.</li>
</ul>
<footer>Files: algeria/04_tool/GBF_3.1_Tool_Algeria_Worked_Example.xlsx (filled tool), with data, scripts, outputs and documents in the algeria folder. Workbook recalculated in Microsoft Excel with zero formula errors.</footer>
</main>
</div>
"""

page = f"""<title>Algeria Indicator 3.1 Walkthrough</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..800&family=IBM+Plex+Mono:wght@400;500&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">
<style>{CSS}</style>
{body}"""
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w").write(page)
print("written", OUT, len(page))
