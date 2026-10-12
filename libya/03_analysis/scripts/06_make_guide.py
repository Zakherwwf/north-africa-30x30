"""Generate the illustrated Libya walkthrough for the Indicator 3.1 tool (numbers from the Excel-recalculated workbook)."""
import csv, json, html, os
from shapely.geometry import shape, mapping

HERE = os.path.dirname(os.path.abspath(__file__))
OUTD = f"{HERE}/../outputs"
OUT = os.path.abspath(f"{HERE}/../../05_guide/Libya_Indicator_3.1_Guide.html")
geo = json.load(open(f"{OUTD}/geom_moll_simplified.json"))
kgeo = json.load(open(f"{OUTD}/kba_geom_moll_simplified.json"))
cfg = json.load(open(f"{OUTD}/tool_config_libya.json"))
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
R = dict(land=1630170.14, sea=357322.93, pa_t=2099.334, pa_m=2241.06, cov_t=0.001287800548, cov_m=0.00627180573,
         need_t=486951.708, need_m=104955.819)
# (year, land % with OECMs, land % PAs only, sea %)
ts = [(1970, 0, 0, 0), (1976, .0012, .0012, 0), (1978, .0209, .0209, 0), (1992, .1287, .1287, .6272), (2000, .1288, .1288, .6272), (2026, .1288, .1288, .6272)]


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
sb = 300 * 1000 * k
scalebar = (f'<g font-size="11" fill="var(--ink-2)"><rect x="12" y="{H - 16}" width="{sb:.1f}" height="4" fill="var(--ink-2)"/>'
            f'<text x="{12 + sb + 6:.1f}" y="{H - 11}">300 km</text></g>')


def svgmap(inner, label):
    return f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{e(label)}">{base}{inner}{scalebar}</svg>'


def kcol(p):
    return "var(--accent)" if p >= 98 else "var(--kmid)" if p >= 50 else "var(--gap)" if p > 0 else "var(--kzero)"


kpaths = "".join(f'<path d="{path(kk["geom"])}" fill="{kcol(kk["pct"])}" fill-opacity="0.9" stroke="var(--ink)" stroke-width="0.4">'
                 f'<title>{e(kk["name"])}: {kk["pct"]:.1f}% covered</title></path>' for kk in sorted(kgeo["kba"], key=lambda kk: -kk["pct"]))
ghost = (f'<path d="{path(simp(geo["pa_t"], 1500))}" fill="none" stroke="var(--ink-2)" stroke-width="0.5" stroke-dasharray="2 2"/>'
         f'<path d="{path(simp(geo["oe_t"], 2500))}" fill="none" stroke="var(--oecm)" stroke-width="0.5" stroke-dasharray="2 2"/>')
legend = ('<ul class="legend"><li><i style="background:var(--nat)"></i>National PA</li><li><i style="background:var(--intl)"></i>International PA '
          '(Ramsar)</li><li><i style="background:var(--reg)"></i>Regional PA (SPAMI)</li><li><i style="background:var(--oecm)"></i>OECM</li></ul>')
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


setup_rows = [(4, "Country / jurisdiction", "Libya"), (5, "ISO3 code", "LBY"), (6, "Reporting year", "2026"),
              (7, "WDPA / WD-OECM release used", "WDPA/WD-OECM October 2026"), (8, "KBA dataset version", "World Database of KBAs, September 2026"),
              (9, "Base map used", "geoBoundaries ADM0 + Marine Regions EEZ v12 (Libyan EEZ), Mollweide"), (10, "Terrestrial area (km²)", "1,630,170.14"),
              (11, "Marine & coastal area (km²)", "357,322.93"), (12, "Target coverage", "30.0%"), (14, "PA layer flattened in GIS?", "Y"),
              (15, "OECM layer: PA overlap erased?", "Y  (no OECMs)"), (16, "Mollweide equal-area?", "Y"), (17, "Overlaps attributed to earliest site?", "Y  (no overlaps)"),
              (26, "PAME validity window (years)", "5"), (27, "Time-series start year", "1970")]
setup_mock = mock("Setup", [("A", "Parameter"), ("B", "Value")], [(r, [(l, "lab"), (v, "in")]) for r, l, v in setup_rows], " rows 4–27 (selection)")

reg_rows = []
for i, r in enumerate(cfg["register"]):
    radius = (r[11] / 3.141592653589793) ** 0.5
    reg_rows.append((5 + i, [(r[0], "in"), (r[1], "in"), (r[2], "in"), (r[5], "in"), (r[8], "in"), (r[9], "in"), (r[10], "in"), (f2(r[11], 2), "in"),
                             (f2(r[17], 2), "in"), (f2(r[18], 2), "in"), (1, "calc"), (f"{radius:.2f}", "calc"), ("Buffered point – coverage approximate", "warn")]))
reg_mock = mock("PA_OECM_Register", [("A", "SITE_ID"), ("B", "NAME"), ("C", "DESIG_ENG"), ("F", "IUCN"), ("I", "STATUS_YR"), ("J", "MARINE"),
                                     ("K", "Geometry"), ("L", "REP_AREA km²"), ("R", "NET terr. km²"), ("S", "NET marine km²"), ("Z", "Included"),
                                     ("AI", "Buffer radius km"), ("AL", "QC flags")], reg_rows, " all 5 rows")

head_mock = mock("Headline_3.1", [("A", "Realm"), ("B", "Realm km²"), ("E", "PA used"), ("F", "OECM used"), ("J", "Indicator 3.1"),
                                  ("L", "Gap (pp)"), ("M", "Extra km²"), ("N", "Status")],
                 [(6, [("Terrestrial & inland waters", "lab"), ("1,630,170.14", "calc"), ("2,099.33", "calc"), ("0.00", "calc"), ("0.13%", "key"),
                       ("29.9", "calc"), ("486,951.71", "calc"), ("Below target", "warn")]),
                  (7, [("Marine & coastal", "lab"), ("357,322.93", "calc"), ("2,241.06", "calc"), ("0.00", "calc"), ("0.63%", "key"),
                       ("29.4", "calc"), ("104,955.82", "calc"), ("Below target", "warn")])], " section A")

eco = list(csv.DictReader(open(f"{OUTD}/ecoregion_coverage.csv")))
meow = list(csv.DictReader(open(f"{OUTD}/marine_ecoregion_coverage.csv")))
eco_rows = []
for i, u in enumerate(sorted(eco, key=lambda x: -float(x["extent_km2"])) + sorted(meow, key=lambda x: -float(x["extent_km2"]))):
    ext, p = float(u["extent_km2"]), float(u["pa_km2"])
    eco_rows.append((58 + i, [(u.get("eco_name") or u["ecoregion"], "in"), (f2(ext, 0), "in"), (f2(p, 1), "in"), (f"{p / ext:.2%}", "key"),
                              ("No", "warn")]))
eco_mock = mock("Ecosystems", [("C", "Ecoregion"), ("F", "Extent km²"), ("G", "PA km²"), ("J", "Coverage"), ("K", "≥ 30%?")],
                eco_rows, " section D: 9 terrestrial and 3 marine ecoregions")
biome_mock = mock("Ecosystems", [("A", "GET"), ("C", "Biome / component"), ("F", "Extent"), ("G", "PA"), ("J", "Coverage")],
                  [(8, [("T3", "lab"), ("Shrublands and shrub-dominated woodlands", "lab"), ("63,967", "in"), ("2,079", "in"), ("3.2%", "key")]),
                   (10, [("T5", "lab"), ("Deserts and semi-deserts", "lab"), ("1,565,128", "in"), ("0", "in"), ("0.0%", "key")]),
                   (52, [("Rivers", "lab"), ("Rivers and streams (HydroRIVERS, km)", "lab"), ("407,951", "in"), ("465", "in"), ("0.1%", "key")]),
                   (53, [("Wetlands", "lab"), ("Lakes and wetlands (GLWD v2, km²)", "lab"), ("6,877", "in"), ("23", "in"), ("0.3%", "key")])],
                  " sections A and C")

kba_by = {r[0]: r for r in cfg["kba"]}
krow = {r[0]: 16 + i for i, r in enumerate(cfg["kba"])}
kba_rows = []
for sid in [6474, 6471, 31679, 31705, 31924, 29320, 31957, 6473, 31817, 31807, 6470, 6477]:
    r = kba_by[sid]
    p = min(1, r[7] / r[2])
    kba_rows.append((krow[sid], [(r[0], "in"), (r[1], "in"), (f2(r[2], 1), "in"), (f2(r[3], 2), "in"), (r[6], "in"), (f2(r[7], 1), "in"),
                                 (f"{p:.1%}", "key"), ("Partial" if p > 0 else "None", "calc" if p > 0 else "warn")]))
kba_mock = mock("KBA_Coverage", [("A", "SitRecID"), ("B", "KBA name"), ("C", "Area km²"), ("D", "Ocean frac."), ("G", "Mountain"),
                                 ("H", "PA km²"), ("L", "% covered"), ("O", "Class")], kba_rows, " 12 of 18 rows, all values from the KBA polygons")
kba_sum = mock("KBA_Coverage", [("A", "KBA group"), ("B", "SDG"), ("C", "KBAs"), ("D", "Mean % covered"), ("G", "None"), ("H", "Partial"), ("I", "Complete")],
               [(6, [("All KBAs", "lab"), ("—", "calc"), ("18", "calc"), ("0.3%", "key"), ("16", "calc"), ("2", "calc"), ("0", "calc")]),
                (7, [("Terrestrial KBAs", "lab"), ("15.1.2", "calc"), ("17", "calc"), ("0.3%", "key"), ("15", "calc"), ("2", "calc"), ("0", "calc")]),
                (8, [("Freshwater KBAs", "lab"), ("15.1.2", "calc"), ("0", "calc"), ("–", "calc"), ("0", "calc"), ("0", "calc"), ("0", "calc")]),
                (9, [("Marine KBAs (≥5% ocean)", "lab"), ("14.5.1", "calc"), ("7", "calc"), ("0.0%", "key"), ("7", "calc"), ("0", "calc"), ("0", "calc")]),
                (10, [("Mountain KBAs", "lab"), ("15.4.1", "calc"), ("1", "calc"), ("2.8%", "key"), ("0", "calc"), ("1", "calc"), ("0", "calc")])],
               " section A (results)")

qc = [("Realm areas entered", "Both", "PASS"), ("PA layer flattened", "Y", "PASS"), ("Mollweide projection", "Y", "PASS"),
      ("Included sites without flattened net area", "0", "PASS"), ("Terrestrial coverage ≤ 100%", "0.13%", "PASS"), ("Marine coverage ≤ 100%", "0.63%", "PASS"),
      ("Included sites with any QC flag", "5", "WARN"), ("Included point (buffered) sites", "5", "INFO"),
      ("Share of area with GOV_TYPE not reported", "0.0%", "PASS"), ("Governance total = headline total", "0.000", "PASS"),
      ("KBAs with covered area > KBA area", "0", "PASS")]
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


def tschart():
    w, h, l, r, t, b = 560, 230, 44, 16, 16, 30
    sx = lambda y: l + (y - 1970) / (2030 - 1970) * (w - l - r)
    sy = lambda v: t + (1 - v / 1.0) * (h - t - b)
    grid = "".join(f'<line x1="{l}" x2="{w - r}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" stroke="var(--line)"/><text x="{l - 6}" y="{sy(v) + 4:.1f}" text-anchor="end">{v:.2g}%</text>' for v in (0, 0.25, 0.5, 0.75, 1.0))
    xt = "".join(f'<text x="{sx(y):.1f}" y="{h - 10}" text-anchor="middle">{y}</text>' for y in (1970, 1980, 1990, 2000, 2010, 2020, 2030))

    def step(idx):
        pts = []
        for i, row in enumerate(ts):
            if i:
                pts.append(f"{sx(row[0]):.1f},{sy(ts[i - 1][idx]):.1f}")
            pts.append(f"{sx(row[0]):.1f},{sy(row[idx]):.1f}")
        return " ".join(pts)
    return f'''<svg viewBox="0 0 {w} {h}" role="img" aria-label="Coverage over time 1970 to 2026, axis to 1 percent" class="chart">{grid}{xt}
<polyline points="{step(1)}" fill="none" stroke="var(--accent)" stroke-width="2.5"/>
<polyline points="{step(3)}" fill="none" stroke="var(--intl)" stroke-width="2.5"/>
<text x="{sx(2026) - 6:.1f}" y="{sy(0.1288) - 8:.1f}" text-anchor="end" class="val" style="fill:var(--accent)">land 0.13%</text>
<text x="{sx(2026) - 6:.1f}" y="{sy(0.6272) - 8:.1f}" text-anchor="end" class="val" style="fill:var(--intl)">sea 0.63%</text>
<text x="{sx(1978) + 4:.1f}" y="{sy(0.03) - 8:.1f}" class="lab">1976–78: Bier Ayad, Wadi El Kouf</text>
<text x="{sx(1992) + 4:.1f}" y="{sy(0.6272) + 16:.1f}" class="lab">1992: El Nagaza</text>
<text x="{w - r}" y="{t + 10}" text-anchor="end" class="lab">axis 0–1% (target line at 30% is off the chart)</text></svg>'''


steps = [("data", "Collect the data"), ("setup", "Fill in Setup"), ("points", "The points-only problem"), ("register", "Enter the site register"),
         ("headline", "Read the headline"), ("eco", "Ecosystems and inland waters"), ("kba", "Key Biodiversity Areas"), ("gov", "Governance and effectiveness"),
         ("ts", "Time series"), ("qc", "Quality checks and reconciliation"), ("report", "Report"), ("gaps", "What this example leaves out")]
nav = "".join(f'<li><a href="#{a}"><span>{i + 1:02d}</span>{e(t)}</a></li>' for i, (a, t) in enumerate(steps))


def head(i, title, sheet=None):
    chip = f'<span class="chip">{e(sheet)}</span>' if sheet else ""
    return f'<section class="step" id="{steps[i][0]}"><div class="stephead"><span class="num">STEP {i + 1:02d}</span>{chip}</div><h2>{e(title)}</h2>'


cellkey = ('<div class="cellkey"><span><i style="background:var(--in-bg)"></i>Input you type or paste</span><span><i style="background:var(--calc-bg)"></i>Formula, computed by the tool</span>'
           '<span><i style="background:var(--key-bg)"></i>Key result</span><span><i style="background:var(--warn-bg)"></i>Flag to act on</span></div>')
circles = (f'<path d="{path(simp(geo["pa_t"], 300))}" fill="var(--accent)" fill-opacity="0.9" stroke="var(--accent)" stroke-width="1.5"/>'
           f'<path d="{path(geo["pa_m"])}" fill="var(--intl)" fill-opacity="0.9" stroke="var(--intl)" stroke-width="1.5"/>')
legend_c = ('<ul class="legend"><li><i style="background:var(--accent)"></i>Circles on land</li><li><i style="background:var(--intl)"></i>Circles at sea</li>'
            '<li><i style="background:var(--sea);border:1px solid var(--sea-line)"></i>Libyan EEZ</li></ul>')

body = f"""
<div class="wrap">
<nav class="index" aria-label="Steps"><p class="lbl">Walkthrough</p><ol>{nav}</ol></nav>
<main>
<header class="hero">
<div class="eyebrow">GBF Headline Indicator 3.1 · National worked example with real data</div>
<h1>Libya, step by step through the 30×30 tool</h1>
<p class="lede">This guide fills the Indicator 3.1 Excel tool for Libya from the 5 records in the October 2026 World Database on Protected Areas, the 18 official Key Biodiversity Area polygons (September 2026), and a GIS run over land and sea. Every number comes from those data and from the workbook recalculated in Excel.</p>
<p>Libya is the opposite of the large-OECM cases. The WDPA holds only five sites, all as points with a reported area, and no OECMs. The tool still works, but every figure rests on circles drawn around five coordinates, and the main finding is a data gap: the reserves Libya has declared since 2010 have not reached the global database.</p>
<div class="facts six">
<div><b>5</b><small>WDPA records, all points; 0 OECMs</small></div>
<div><b>0.13%</b><small>of 1,630,170 km² of land</small></div>
<div><b>0.63%</b><small>of 357,323 km² of sea</small></div>
<div><b>486,952 km²</b><small>of land still needed for 30%</small></div>
<div><b>104,956 km²</b><small>of sea still needed for 30%</small></div>
<div><b>0.3%</b><small>average coverage of 18 KBAs</small></div>
</div>
</header>

{head(0, "Collect the data")}
<ol class="do">
<li><b>Protected areas.</b> WDPA, October 2026, from the UNEP-WCMC map service behind <a href="https://www.protectedplanet.net/country/LBY">Protected Planet</a>: five point records and no polygons. The WD-OECM has no Libyan records.</li>
<li><b>Base map.</b> Land: the geoBoundaries ADM0 outline. Sea: the Marine Regions EEZ v12 "Libyan Exclusive Economic Zone", as used by Protected Planet; the 8,114 km² zone claimed by both Egypt and Libya is kept for reference only. Coastal gaps (176 km²) are closed.</li>
<li><b>Key Biodiversity Areas.</b> The World Database of KBAs, September 2026: 18 Libyan polygons and 51 trigger-species records. Licensed data; don't republish the polygons.</li>
<li><b>Management effectiveness.</b> No GD-PAME evaluation is listed for any of the five sites.</li>
<li><b>Ecosystems and inland waters.</b> RESOLVE Ecoregions 2017, Marine Ecoregions of the World, GMBA v2.0, HydroRIVERS and GLWD v2, clipped by <code>00_prepare_layers.py</code>.</li>
<li><b>National documents.</b> Libya's National Biodiversity Strategy and Action Plan 2023–2030. No CBD national report could be retrieved.</li>
</ol>

{head(1, "Fill in Setup", "Sheet: Setup")}
{setup_mock}
{cellkey}

{head(2, "The points-only problem", "Outside Excel: 03_analysis/scripts/01_gis_flatten.py")}
<p>When a site has no boundary, the metadata says to draw a circle with the reported area around the reported point. For Libya that is the whole method: the five circles are the protected-area layer. They don't overlap, so flattening changes nothing.</p>
<div class="maps one"><figure><figcaption><b>Five circles</b>Each site drawn as a circle of its reported area around its reported point</figcaption>{svgmap(circles, "Five buffered protected-area points in Libya")}{legend_c}</figure></div>
<div class="pitfall"><h3>Why this matters</h3>
<p>A circle can't follow a coastline or a valley. El Nagaza National Park is reported as 4,000 km² and as marine; its circle, 35.7 km in radius around 32.67°N 14.28°E, falls 1,759 km² on land and 2,241 km² at sea. That single site is 84% of the land figure and all of the sea figure. A real boundary for El Nagaza, or for Wadi El Kouf in the Jabal al Akhdar, would change the result more than any other step in this guide.</p>
<p>The register flags all five sites "Buffered point – coverage approximate". The fix is a data fix: send UNEP-WCMC the boundaries.</p></div>

{head(3, "Enter the site register", "Sheet: PA_OECM_Register")}
{reg_mock}
<p>Column AI shows the radius the tool derives from the reported area (√(area/π)). The two Ramsar springs, Ain Elshakika and Ain Elzarga, are under 1 km² each.</p>

{head(4, "Read the headline", "Sheet: Headline_3.1")}
{head_mock}
<div class="result"><div><strong>Result.</strong> Protected areas cover <b>0.13%</b> of Libya's land (2,099 km²) and <b>0.63%</b> of its waters (2,241 km²). Reaching 30% would take another <b>486,952 km²</b> on land and <b>104,956 km²</b> at sea. Libya's own target 3 in its NBSAP is the same 30% by 2030.</div></div>

{head(5, "Ecosystems and inland waters", "Sheet: Ecosystems")}
{eco_mock}
{biome_mock}
<div class="result"><div><strong>Finding.</strong> Seven of Libya's nine land ecoregions, and 96% of its land, have no protection at all; the deserts (biome T5, 1.57 million km²) are at 0%. The two Mediterranean ecoregions of the coast reach 2.5% and 3.4%. Of the 4,997 km² of salt pans and sebkhas, the country's main wetland type, none lies in a protected area; all lakes and wetlands together are 0.3% covered.</div></div>

{head(6, "Key Biodiversity Areas", "Sheet: KBA_Coverage · script 02_kba_overlay.py")}
<div class="maps one"><figure><figcaption><b>18 KBAs by share covered</b>Official KBA polygons, September 2026</figcaption>{svgmap(ghost + kpaths, "Key Biodiversity Areas of Libya coloured by covered share")}{klegend}</figure></div>
{kba_mock}
{kba_sum}
<div class="result"><div><strong>Finding.</strong> Sixteen of Libya's 18 KBAs have no protection. The two that do are covered only by circles: Jabal al Akhdar (11,106 km²) by the Wadi El Kouf circle, 2.9%; and Nefhusa (13,421 km²) by the land half of the El Nagaza circle, 2.8%. The seven marine KBAs, including the Gulf of Sirte, Bumbah Gulf and Farwa Island, are at 0%.</div></div>
<p>The KBA database itself reports 0% for every Libyan KBA, because it doesn't buffer point-only protected areas. That is the only difference between the two sources. Two foreign KBAs overlap Libyan land along the borders: Tassili n'Ajjer in Algeria (552 km²) and Sallum in Egypt (39 km²); they are listed in <code>kba_foreign_overlapping_LBY.csv</code> and not counted.</p>

{head(7, "Governance and effectiveness", "Sheets: Governance, Mgmt_Effectiveness")}
<p>All five sites are governed by the national government, and none has a recorded management-effectiveness evaluation, so 100% of the covered area is "Not assessed". The two Ramsar records state that their management plans are "not implemented and not available".</p>

{head(8, "Time series", "Sheet: Time_Series")}
{tschart()}
<p>Coverage was set by three designations: Bier Ayad (1976), Wadi El Kouf (1978) and El Nagaza (1992); the two Ramsar springs (2000) add under 1 km². Nothing designated since 2000 appears in the WDPA.</p>

{head(9, "Quality checks and reconciliation", "Sheet: QC_Checks")}
{qc_mock}
<div class="scroll"><table class="recon"><thead><tr><th></th><th>Land</th><th>Sea</th></tr></thead><tbody>
<tr><td>This workbook (geoBoundaries + Libyan EEZ)</td><td>2,099 of 1,630,170 km² = 0.13%</td><td>2,241 of 357,323 km² = 0.63%</td></tr>
<tr><td>Protected Planet, October 2026</td><td>2,075 of 1,616,513 km² = 0.13%</td><td>2,269 of 357,423 km² = 0.63%</td></tr>
<tr><td>Libya NBSAP 2023–2030</td><td>11 reserves by 2010, about 0.16% of the territory; 22 new reserves, 6 wetlands and 2 wildlife sites announced in 2021</td><td>–</td></tr>
</tbody></table></div>
<p>The workbook matches Protected Planet. The NBSAP describes a larger network: 11 reserves by 2010 and 30 new sites announced in 2021, none of which is in the WDPA. Until they are reported to UNEP-WCMC with boundaries, they can't enter the global indicator. Submitting them is the single most useful step Libya can take for Target 3 reporting.</p>

{head(10, "Report", "Sheet: Dashboard")}
<blockquote class="draft">In 2026, the protected areas reported in the WDPA covered 2,099 km², or 0.13% of Libya's terrestrial and inland water area, and 2,241 km², or 0.63% of its marine and coastal area (Headline Indicator 3.1; WDPA October 2026; Mollweide equal-area). All five sites are recorded as points, so these areas are approximations; no OECMs have been reported. Reaching 30% would require a further 486,952 km² on land and 104,956 km² at sea. Sixteen of Libya's 18 Key Biodiversity Areas have no protection. Reserves declared nationally since 2010, including 22 announced in 2021, are not yet included in the WDPA.</blockquote>

{head(11, "What this example leaves out")}
<ol class="do">
<li><b>Libya's national network.</b> The reserves, wetlands and wildlife sites announced in 2021 are not in the WDPA; with their boundaries the whole workbook would change.</li>
<li><b>Real boundaries for the five sites.</b> The circles are a stand-in required by the method.</li>
<li><b>OECMs.</b> None reported; candidates could include traditionally managed oases and grazing reserves, if they meet the CBD 14/8 criteria.</li>
<li><b>Marine biomes and effectiveness scores.</b> Bathymetry and assessment data are not available here.</li>
</ol>

<h3>Sources</h3>
<ul class="sources">
<li>UNEP-WCMC &amp; IUCN (2026). <a href="https://www.protectedplanet.net/country/LBY">Protected Planet: Libya</a>, WDPA/WD-OECM October 2026.</li>
<li>GBF Indicators. <a href="https://www.gbf-indicators.org/metadata/headline/3-1">Metadata for Headline Indicator 3.1</a>.</li>
<li>BirdLife International on behalf of the KBA Partnership (2026). World Database of Key Biodiversity Areas, September 2026, and KBA trigger species.</li>
<li>State of Libya, Ministry of Environment (2025). National Biodiversity Strategy and Action Plan 2023–2030.</li>
<li>Flanders Marine Institute (2023). EEZ v12. Runfola, D. et al. (2020). geoBoundaries. Snethlage, M.A. et al. (2022). GMBA Mountain Inventory v2.</li>
<li>Dinerstein, E. et al. (2017). BioScience 67(6): 534–545. Spalding, M.D. et al. (2007). BioScience 57(7): 573–583. Lehner, B. &amp; Grill, G. (2013). HydroRIVERS. Lehner, B. et al. (2025). GLWD v2. ESSD 17: 2277–2329.</li>
</ul>
<footer>Files: libya/04_tool/GBF_3.1_Tool_Libya_Worked_Example.xlsx (filled tool), with data, scripts, outputs and documents in the libya folder. Workbook recalculated in Microsoft Excel with zero formula errors.</footer>
</main>
</div>
"""

page = f"""<title>Libya Indicator 3.1 Walkthrough</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..800&family=IBM+Plex+Mono:wght@400;500&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">
<style>{CSS}</style>
{body}"""
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w").write(page)
print("written", OUT, len(page))
