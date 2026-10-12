"""Generate the illustrated Egypt walkthrough for the Indicator 3.1 tool (numbers from the Excel-recalculated workbook)."""
import csv, json, html, os
from shapely.geometry import shape, mapping

HERE = os.path.dirname(os.path.abspath(__file__))
OUTD = f"{HERE}/../outputs"
OUT = os.path.abspath(f"{HERE}/../../05_guide/Egypt_Indicator_3.1_Guide.html")
geo = json.load(open(f"{OUTD}/geom_moll_simplified.json"))
kgeo = json.load(open(f"{OUTD}/kba_geom_moll_simplified.json"))
cfg = json.load(open(f"{OUTD}/tool_config_egypt.json"))
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
R = dict(land=986014.25, sea=243974.16, pa_t=110805.442, pa_m=8821.168, cov_t=0.11237712031, cov_m=0.036156156865,
         need_t=184998.833, need_m=64371.08)
# (year, land % with OECMs, land % PAs only, sea %)
ts = [(1975, 0, 0, 0), (1983, .0199, .0199, .1740), (1988, .0909, .0909, .3202), (1989, .4118, .4118, .3202), (1995, 1.4701, 1.4701, 1.3113),
      (1996, 4.0210, 4.0210, 1.4778), (1998, 4.3693, 4.3693, 1.4839), (2002, 5.4771, 5.4771, 1.4839), (2003, 5.9339, 5.9339, 2.8032),
      (2006, 5.9416, 5.9416, 3.4797), (2007, 11.2153, 11.2153, 3.4797), (2010, 11.2362, 11.2362, 3.6156), (2012, 11.2377, 11.2377, 3.6156),
      (2026, 11.2377, 11.2377, 3.6156)]


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
          '(Ramsar, World Heritage)</li></ul>')
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


setup_rows = [(4, "Country / jurisdiction", "Egypt"), (5, "ISO3 code", "EGY"), (6, "Reporting year", "2026"),
              (7, "WDPA / WD-OECM release used", "WDPA/WD-OECM October 2026"), (8, "KBA dataset version", "World Database of KBAs, September 2026"),
              (9, "Base map used", "geoBoundaries ADM0 minus Halaib + Marine Regions EEZ v12 (Egyptian EEZ), Mollweide"), (10, "Terrestrial area (km²)", "986,014.25"),
              (11, "Marine & coastal area (km²)", "243,974.16"), (12, "Target coverage", "30.0%"), (14, "PA layer flattened in GIS?", "Y"),
              (15, "OECM layer: PA overlap erased?", "Y  (no OECMs)"), (16, "Mollweide equal-area?", "Y"), (17, "Overlaps attributed to earliest site?", "Y"),
              (26, "PAME validity window (years)", "5"), (27, "Time-series start year", "1975")]
setup_mock = mock("Setup", [("A", "Parameter"), ("B", "Value")], [(r, [(l, "lab"), (v, "in")]) for r, l, v in setup_rows], " rows 4–27 (selection)")

sel = [9782, 312977, 14895, 61414, 555543023, 30006, 555547985, 902487, 17724, 17725, 306581, 555543022, 306589, 555543027, 555543036]
rowno = {r: 5 + i for i, r in enumerate(reg)}
reg_rows = []
for sid in sel:
    r = reg[sid]
    excl = "UNESCO-MAB Biosphere Reserve" if r[15] == "Y" else ("STATUS = Proposed" if r[7] == "Proposed" else "")
    reg_rows.append((rowno[sid], [(r[0], "in"), (r[1], "in"), (r[2], "in"), (r[6], "in"), (r[7], "in"), (r[8], "in"), (r[10], "in"),
                                  (f2(r[17], 1), "in"), (f2(r[18], 1), "in"), (r[21], "in"),
                                  (0 if excl else 1, "warn" if excl else "calc"), (excl, "warn" if excl else "calc")]))
reg_mock = mock("PA_OECM_Register", [("A", "SITE_ID"), ("B", "NAME"), ("C", "DESIG_ENG"), ("G", "GOV_TYPE"), ("H", "STATUS"), ("I", "STATUS_YR"),
                                     ("K", "Geometry"), ("R", "NET terr. km²"), ("S", "NET marine km²"), ("V", "PAME yr"),
                                     ("Z", "Included"), ("AA", "Exclusion reason")], reg_rows, " 15 of the 50 real rows, chosen to show each rule")

head_mock = mock("Headline_3.1", [("A", "Realm"), ("B", "Realm km²"), ("E", "PA used"), ("F", "OECM used"), ("J", "Indicator 3.1"),
                                  ("L", "Gap (pp)"), ("M", "Extra km²"), ("N", "Status")],
                 [(6, [("Terrestrial & inland waters", "lab"), ("986,014.25", "calc"), ("110,805.44", "calc"), ("0.00", "calc"), ("11.24%", "key"),
                       ("18.8", "calc"), ("184,998.83", "calc"), ("Below target", "warn")]),
                  (7, [("Marine & coastal", "lab"), ("243,974.16", "calc"), ("8,821.17", "calc"), ("0.00", "calc"), ("3.62%", "key"),
                       ("26.4", "calc"), ("64,371.08", "calc"), ("Below target", "warn")])], " section A")

eco = [u for u in csv.DictReader(open(f"{OUTD}/ecoregion_coverage.csv")) if float(u["extent_km2"]) >= 100]
meow = list(csv.DictReader(open(f"{OUTD}/marine_ecoregion_coverage.csv")))
eco_rows = []
for i, u in enumerate(sorted(eco, key=lambda x: -float(x["extent_km2"])) + sorted(meow, key=lambda x: -float(x["extent_km2"]))):
    ext, p = float(u["extent_km2"]), float(u["pa_km2"])
    eco_rows.append((58 + i, [(u.get("eco_name") or u["ecoregion"], "in"), (f2(ext, 0), "in"), (f2(p, 0), "in"), (f"{p / ext:.1%}", "key"),
                              ("Yes" if p / ext >= 0.3 else "No", "pass" if p / ext >= 0.3 else "warn")]))
eco_mock = mock("Ecosystems", [("C", "Ecoregion"), ("F", "Extent km²"), ("G", "PA km²"), ("J", "Coverage"), ("K", "≥ 30%?")],
                eco_rows, " section D: terrestrial ecoregions over 100 km² and marine ecoregions")
biome_mock = mock("Ecosystems", [("A", "GET"), ("C", "Biome / component"), ("F", "Extent"), ("G", "PA"), ("J", "Coverage")],
                  [(8, [("T3", "lab"), ("Shrublands and shrub-dominated woodlands", "lab"), ("3,661", "in"), ("287", "in"), ("7.8%", "key")]),
                   (10, [("T5", "lab"), ("Deserts and semi-deserts (incl. Nile Delta, see text)", "lab"), ("980,516", "in"), ("109,821", "in"), ("11.2%", "key")]),
                   (52, [("Rivers", "lab"), ("Rivers and streams (HydroRIVERS, km)", "lab"), ("226,820", "in"), ("24,029", "in"), ("10.6%", "key")]),
                   (53, [("Wetlands", "lab"), ("Lakes and wetlands (GLWD v2, km²)", "lab"), ("44,570", "in"), ("2,238", "in"), ("5.0%", "key")])],
                  " sections A and C")
wg = [x for x in csv.DictReader(open(f"{OUTD}/glwd_wetland_coverage_by_group.csv")) if x["counted"] == "Y" and float(x["extent_km2"]) >= 1]
wet_mock = mock("GLWD v2 · outputs/glwd_wetland_coverage_by_group.csv", [("", "Wetland group"), ("", "Extent km²"), ("", "PA km²"), ("", "Coverage")],
                [(i + 1, [(x["group"], "lab"), (f2(float(x["extent_km2"]), 0), "calc"), (f2(float(x["pa_km2"]), 0), "calc"),
                          (f'{float(x["pa_pct"]):.1f}%', "key")]) for i, x in enumerate(wg)]
                + [("Σ", [("Lakes and wetlands → Ecosystems row 53", "lab"), ("44,570", "calc"), ("2,238", "calc"), ("5.0%", "key")])], " GIS output")

kba_by = {r[0]: r for r in cfg["kba"]}
krow = {r[0]: 16 + i for i, r in enumerate(cfg["kba"])}
kba_rows = []
for sid in [6211, 6219, 6195, 6196, 30814, 6192, 6201, 6210, 46615, 6200, 6198, 6215]:
    r = kba_by[sid]
    p = min(1, r[7] / r[2])
    cls = "Complete" if p >= 0.98 else ("Partial" if p > 0 else "None")
    kba_rows.append((krow[sid], [(r[0], "in"), (r[1], "in"), (f2(r[2], 1), "in"), (f2(r[3], 2), "in"), (r[5], "in"), (r[6], "in"), (f2(r[7], 1), "in"),
                                 (f"{p:.1%}", "key"), (cls, "pass" if cls == "Complete" else ("warn" if cls == "None" else "calc"))]))
kba_mock = mock("KBA_Coverage", [("A", "SitRecID"), ("B", "KBA name"), ("C", "Area km²"), ("D", "Ocean frac."), ("F", "Freshw."), ("G", "Mountain"),
                                 ("H", "PA km²"), ("L", "% covered"), ("O", "Class")], kba_rows, " 12 of 33 rows, all values from the KBA polygons")
kba_sum = mock("KBA_Coverage", [("A", "KBA group"), ("B", "SDG"), ("C", "KBAs"), ("D", "Mean % covered"), ("G", "None"), ("H", "Partial"), ("I", "Complete")],
               [(6, [("All KBAs", "lab"), ("—", "calc"), ("33", "calc"), ("35.2%", "key"), ("15", "calc"), ("10", "calc"), ("8", "calc")]),
                (7, [("Terrestrial KBAs", "lab"), ("15.1.2", "calc"), ("31", "calc"), ("32.7%", "key"), ("15", "calc"), ("9", "calc"), ("7", "calc")]),
                (8, [("Freshwater KBAs", "lab"), ("15.1.2", "calc"), ("11", "calc"), ("26.3%", "key"), ("7", "calc"), ("2", "calc"), ("2", "calc")]),
                (9, [("Marine KBAs (≥5% ocean)", "lab"), ("14.5.1", "calc"), ("13", "calc"), ("52.3%", "key"), ("3", "calc"), ("6", "calc"), ("4", "calc")]),
                (10, [("Mountain KBAs", "lab"), ("15.4.1", "calc"), ("7", "calc"), ("40.0%", "key"), ("4", "calc"), ("1", "calc"), ("2", "calc")])],
               " section A (results)")

gov_mock = mock("Governance", [("A", "IUCN governance type"), ("B", "Sites"), ("C", "Terr. km²"), ("G", "% of covered land"), ("J", "Marine km²")],
                [(6, [("A. Governance by government", "lab"), ("23", "calc"), ("57,746.29", "calc"), ("52.1%", "key"), ("6,481.53", "calc")]),
                 (7, [("B–D. Shared, private, IPLC", "lab"), ("0", "calc"), ("0", "calc"), ("0.0%", "calc"), ("0", "calc")]),
                 (10, [("Not reported", "lab"), ("12", "calc"), ("53,059.15", "warn"), ("47.9%", "warn"), ("2,339.64", "warn")]),
                 (11, [("TOTAL", "lab"), ("35", "calc"), ("110,805.44", "calc"), ("100%", "calc"), ("8,821.17", "calc")])], " section A")

pame_mock = mock("Mgmt_Effectiveness", [("A", "Effectiveness class"), ("B", "Sites"), ("C", "Terr. km²"), ("G", "% of covered land"), ("J", "Marine km²")],
                 [(6, [("High / Moderate / Low (scored)", "lab"), ("0", "calc"), ("0", "calc"), ("0.0%", "calc"), ("0", "calc")]),
                  (9, [("Assessed – no score (Wadi Al-Hitan, 2025)", "lab"), ("1", "calc"), ("13.07", "key"), ("0.01%", "key"), ("0", "calc")]),
                  (10, [("Assessment outdated (2001–2014)", "lab"), ("24", "calc"), ("57,808.94", "warn"), ("52.2%", "warn"), ("8,131.99", "warn")]),
                  (11, [("Not assessed", "lab"), ("10", "calc"), ("52,983.44", "calc"), ("47.8%", "calc"), ("689.18", "calc")])], " section A (selection)")

qc = [("Realm areas entered", "Both", "PASS"), ("PA layer flattened", "Y", "PASS"), ("Mollweide projection", "Y", "PASS"),
      ("Included sites without flattened net area", "0", "PASS"), ("Terrestrial coverage ≤ 100%", "11.24%", "PASS"), ("Marine coverage ≤ 100%", "3.62%", "PASS"),
      ("Included sites with any QC flag", "16", "WARN"), ("Included point (buffered) sites", "2", "INFO"),
      ("Share of area with GOV_TYPE not reported", "46.3%", "WARN"), ("Governance total = headline total", "0.000", "PASS"),
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


def bars():
    w, h = 560, 150
    rows = [("Land: sum of site areas", 114426, "var(--gap)"), ("Land: after flattening", 110805, "var(--accent)"),
            ("Sea: sum of site areas", 8838, "var(--gap)"), ("Sea: after flattening", 8821, "var(--intl)")]
    sx = lambda v: 210 + v / 125000 * (w - 300)
    out = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Gross versus flattened protected area, land and sea" class="chart">']
    for i, (lab, v, c) in enumerate(rows):
        y = 6 + i * 36
        out.append(f'<text x="200" y="{y + 17}" text-anchor="end" class="lab">{lab}</text><rect x="210" y="{y}" width="{max(2, sx(v) - 210):.1f}" height="24" rx="2" fill="{c}"/>'
                   f'<text x="{sx(v) + 6:.1f}" y="{y + 17}" class="val">{v:,.0f} km²</text>')
    return "".join(out) + "</svg>"


def tschart():
    w, h, l, r, t, b = 560, 240, 44, 16, 16, 30
    sx = lambda y: l + (y - 1975) / (2030 - 1975) * (w - l - r)
    sy = lambda v: t + (1 - v / 32) * (h - t - b)
    grid = "".join(f'<line x1="{l}" x2="{w - r}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" stroke="var(--line)"/><text x="{l - 6}" y="{sy(v) + 4:.1f}" text-anchor="end">{v}%</text>' for v in (0, 10, 20, 30))
    xt = "".join(f'<text x="{sx(y):.1f}" y="{h - 10}" text-anchor="middle">{y}</text>' for y in (1980, 1990, 2000, 2010, 2020, 2030))

    def step(idx):
        pts = []
        for i, row in enumerate(ts):
            if i:
                pts.append(f"{sx(row[0]):.1f},{sy(ts[i - 1][idx]):.1f}")
            pts.append(f"{sx(row[0]):.1f},{sy(row[idx]):.1f}")
        return " ".join(pts)
    return f'''<svg viewBox="0 0 {w} {h}" role="img" aria-label="Coverage over time 1975 to 2026" class="chart">{grid}{xt}
<line x1="{l}" x2="{w - r}" y1="{sy(30):.1f}" y2="{sy(30):.1f}" stroke="var(--ink)" stroke-dasharray="5 4"/><text x="{l + 4}" y="{sy(30) - 6:.1f}" class="lab">30% by 2030</text>
<line x1="{l}" x2="{w - r}" y1="{sy(20):.1f}" y2="{sy(20):.1f}" stroke="var(--ink-2)" stroke-dasharray="2 4"/><text x="{l + 4}" y="{sy(20) - 6:.1f}" class="lab">national target 20% (NBSAP 2025)</text>
<polygon points="{sx(1975):.1f},{sy(0):.1f} {step(1)} {sx(2026):.1f},{sy(0):.1f}" fill="var(--accent)" fill-opacity="0.14"/>
<polyline points="{step(1)}" fill="none" stroke="var(--accent)" stroke-width="2.5"/>
<polyline points="{step(3)}" fill="none" stroke="var(--intl)" stroke-width="2.5"/>
<text x="{sx(2026) - 6:.1f}" y="{sy(11.24) - 8:.1f}" text-anchor="end" class="val" style="fill:var(--accent)">land 11.24%</text>
<text x="{sx(2026) - 6:.1f}" y="{sy(3.62) + 16:.1f}" text-anchor="end" class="val" style="fill:var(--intl)">sea 3.62%</text>
<text x="{sx(1996) - 4:.1f}" y="{sy(4.02) - 10:.1f}" text-anchor="end" class="lab">1996: Wadi Al Alaqi, St Katherine</text>
<text x="{sx(2007) - 4:.1f}" y="{sy(11.2) - 10:.1f}" text-anchor="end" class="lab">2007: El-Gelf El-Keber</text></svg>'''


steps = [("data", "Collect the data"), ("setup", "Fill in Setup and the Halaib question"), ("gis", "Flatten the overlaps in GIS"),
         ("register", "Enter the site register"), ("headline", "Read the headline"), ("eco", "Ecosystems and inland waters"),
         ("kba", "Key Biodiversity Areas"), ("gov", "Governance"), ("pame", "Management effectiveness"), ("ts", "Time series"),
         ("qc", "Quality checks and reconciliation"), ("report", "Report"), ("gaps", "What this example leaves out")]
nav = "".join(f'<li><a href="#{a}"><span>{i + 1:02d}</span>{e(t)}</a></li>' for i, (a, t) in enumerate(steps))


def head(i, title, sheet=None):
    chip = f'<span class="chip">{e(sheet)}</span>' if sheet else ""
    return f'<section class="step" id="{steps[i][0]}"><div class="stephead"><span class="num">STEP {i + 1:02d}</span>{chip}</div><h2>{e(title)}</h2>'


cellkey = ('<div class="cellkey"><span><i style="background:var(--in-bg)"></i>Input you type or paste</span><span><i style="background:var(--calc-bg)"></i>Formula, computed by the tool</span>'
           '<span><i style="background:var(--key-bg)"></i>Key result</span><span><i style="background:var(--warn-bg)"></i>Flag to act on</span></div>')
flat = (f'<path d="{path(simp(geo["pa_t"], 1200))}" fill="var(--accent)" fill-opacity="0.85" stroke="var(--accent)" stroke-width="0.6"/>'
        f'<path d="{path(simp(geo["pa_m"], 600))}" fill="var(--intl)" fill-opacity="0.85" stroke="var(--intl)" stroke-width="0.6"/>')
legend2 = ('<ul class="legend"><li><i style="background:var(--accent)"></i>Counted on land</li><li><i style="background:var(--intl)"></i>Counted at sea</li>'
           '<li><i style="background:var(--sea);border:1px solid var(--sea-line)"></i>Egyptian EEZ</li></ul>')

body = f"""
<div class="wrap">
<nav class="index" aria-label="Steps"><p class="lbl">Walkthrough</p><ol>{nav}</ol></nav>
<main>
<header class="hero">
<div class="eyebrow">GBF Headline Indicator 3.1 · National worked example with real data</div>
<h1>Egypt, step by step through the 30×30 tool</h1>
<p class="lede">This guide fills the Indicator 3.1 Excel tool for Egypt from the 50 records in the October 2026 World Database on Protected Areas, the 33 official Key Biodiversity Area polygons in Egyptian jurisdiction (September 2026), and a GIS run over land and sea. Every number comes from those data and from the workbook recalculated in Excel.</p>
<p>Egypt has a sizeable network of large desert protectorates and Red Sea parks, no OECMs, and two complications: the Halaib Triangle, claimed by both Egypt and Sudan, holds part of Gebel Elba National Park; and 13 large protected areas proposed in 1999 have never been designated.</p>
<div class="facts six">
<div><b>50</b><small>WDPA records (47 polygons, 3 points), 0 OECMs</small></div>
<div><b>35</b><small>records counted after filtering</small></div>
<div><b>11.24%</b><small>of 986,014 km² of land</small></div>
<div><b>3.62%</b><small>of 243,974 km² of sea</small></div>
<div><b>184,999 km²</b><small>of land still needed for 30%</small></div>
<div><b>35.2%</b><small>average coverage of 33 KBAs</small></div>
</div>
</header>

{head(0, "Collect the data")}
<ol class="do">
<li><b>Protected areas.</b> WDPA, October 2026, from the UNEP-WCMC map service behind <a href="https://www.protectedplanet.net/country/EGY">Protected Planet</a>: 47 polygons and 3 points. The WD-OECM has no Egyptian records.</li>
<li><b>Base map.</b> Land: the geoBoundaries ADM0 outline without the Halaib Triangle (Step 2). Sea: the Marine Regions EEZ v12 "Egyptian Exclusive Economic Zone"; the Halaib and Egypt–Libya overlapping-claim waters are kept for reference. Coastal gaps (404 km²) are closed.</li>
<li><b>Key Biodiversity Areas.</b> The World Database of KBAs, September 2026: 36 Egyptian polygons, of which 3 lie in the Halaib area and are set aside, and their trigger species. Licensed data; don't republish the polygons.</li>
<li><b>Management effectiveness.</b> GD-PAME evaluations on the 50 site pages: 28 carry at least one, mostly a 2006 RAPPAM assessment.</li>
<li><b>Ecosystems and inland waters.</b> RESOLVE Ecoregions 2017, Marine Ecoregions of the World, GMBA v2.0, HydroRIVERS and GLWD v2.</li>
<li><b>National documents.</b> The NBSAP 2015–2030 and the updated NBSAP (2025), and the 5th National Report to the CBD.</li>
</ol>

{head(1, "Fill in Setup and the Halaib question", "Sheet: Setup")}
<p>The geoBoundaries outline for Egypt follows the 22nd parallel and so includes the Halaib Triangle, which Sudan also claims. Marine Regions treats the Halaib waters as an overlapping claim, and Protected Planet's base for Egypt (982,592 km² of land, 242,841 km² of sea) is close to the area without Halaib. The workbook therefore removes the 18,042 km² triangle, taken as the overlap between the geoBoundaries outlines of Egypt and Sudan, from the land and leaves the Halaib waters out of the sea. That gives 986,014 km² of land, within 0.35% of Protected Planet, and 243,974 km² of sea.</p>
<p>The choice matters. Gebel Elba National Park (the "Elba" record, 35,600 km²) lies largely inside the triangle: 14,105 km² of its land is removed, and 3,778 km² of Wadi Al Alaqi. Three KBAs (Gebel Elba, and the Rawabel and Siyal islands) lie in the Halaib land or waters and are set aside. The script <code>07_sensitivity_halaib.py</code> recomputes the indicator with Halaib included: <b>12.81%</b> of 1,004,056 km² of land and <b>4.62%</b> of 263,389 km² of sea. Report whichever matches national practice, and use the same base map for every number.</p>
{setup_mock}
{cellkey}

{head(2, "Flatten the overlaps in GIS", "Outside Excel: 03_analysis/scripts/01_gis_flatten.py")}
<p>Overlaps in Egypt are few but large: the 2012 Ramsar listings of Lake Qarun and Wadi El Rayan repeat the 1989 protectorates almost exactly, and Wadi Al-Hitan World Heritage Site lies inside Wadi El Rayan.</p>
<div class="maps">
<figure><figcaption><b>Before: 35 records</b>Stacked records over the same ground</figcaption>{svgmap(before, "Protected-area records in Egypt")}{legend}</figure>
<figure><figcaption><b>After: one flat layer per realm</b>110,805 km² on land and 8,821 km² at sea, each counted once</figcaption>{svgmap(flat, "Flattened protected-area layer in Egypt")}{legend2}</figure>
</div>
{bars()}
<h3>The procedure (metadata steps 1–6)</h3>
<ol class="do">
<li><b>Filter.</b> 15 records drop out: 13 protected areas with status <i>Proposed</i> since 1999, 56,941 km² in all, among them the Qattara Depression (22,241 km²), Wadi Qena, Kor Kor and Dongol and El-Galala El-Qebalya; and 2 UNESCO biosphere reserves (Omayed, Wadi Allaqi).</li>
<li><b>Buffer points.</b> Two Ramsar points become circles: Lake Bardawil (595 km²) and Lake Burullus (462 km²).</li>
<li><b>Clip and project.</b> Each site is split into land and sea parts against the base map without Halaib, then measured in Mollweide.</li>
<li><b>Dissolve.</b> Land: 114,426 km² summed becomes <b>110,805 km²</b>. Sea: 8,838 km² becomes <b>8,821 km²</b>.</li>
<li><b>Attribute overlaps.</b> The 1989 Qarun and Wadi El Rayan protectorates keep their area; the 2012 Ramsar records keep almost nothing; Wadi Al-Hitan keeps the 13 km² that falls outside the Wadi El Rayan polygon.</li>
</ol>

{head(3, "Enter the site register", "Sheet: PA_OECM_Register")}
{reg_mock}
<p>Many records carry <code>GOV_TYPE = Not Reported</code>, including El-Gelf El-Keber National Park, the largest site (51,998 km²). That has consequences in Step 8.</p>

{head(4, "Read the headline", "Sheet: Headline_3.1")}
{head_mock}
{gauge([(11.2377, "var(--accent)")], "Land", "gap 18.8 points = 184,999 km²")}
{gauge([(3.6156, "var(--intl)")], "Sea", "gap 26.4 points = 64,371 km²")}
<div class="result"><div><strong>Result.</strong> Protected areas cover <b>11.24%</b> of Egypt's land and <b>3.62%</b> of its waters. Reaching 30% would take another <b>184,999 km²</b> on land and <b>64,371 km²</b> at sea. Egypt's own NBSAP (2025) aims lower: 20% for protected areas and OECMs by 2030. Designating the 13 proposed protected areas, about 56,800 km² of land, would by itself bring land coverage to roughly 17%.</div></div>

{head(5, "Ecosystems and inland waters", "Sheet: Ecosystems")}
{eco_mock}
<p>One caution on the biome grouping: the Nile Delta flooded savanna ecoregion, now mostly farmland and towns, belongs to the RESOLVE "Flooded Grasslands" biome, which the crosswalk sends to deserts (T5) with the Saharan salt flats. Read the T5 figure with that in mind.</p>
{biome_mock}
{wet_mock}
<div class="result"><div><strong>Finding.</strong> The Red Sea mountains and coast are the best covered: the Red Sea–Arabian desert shrublands 56.8%, the Red Sea coastal desert 19.0%. The Nile is almost unprotected: the Nile Delta ecoregion is 0.6% covered, riverine wetlands 0.2%, and the Upper Nile and Aswan reservoir KBAs 0%. At sea, the Red Sea ecoregion is 10.8% covered and Egypt's Mediterranean waters (Levantine Sea) 0.4%.</div></div>

{head(6, "Key Biodiversity Areas", "Sheet: KBA_Coverage · script 02_kba_overlay.py")}
<div class="maps one"><figure><figcaption><b>33 KBAs by share covered</b>Official KBA polygons, September 2026 (Halaib KBAs set aside)</figcaption>{svgmap(ghost + kpaths, "Key Biodiversity Areas of Egypt coloured by covered share")}{klegend}</figure></div>
{kba_mock}
{kba_sum}
<div class="result"><div><strong>Finding.</strong> On average, Egypt's KBAs are <b>35.2%</b> covered. Eight are fully covered, among them St Katherine, Ras Mohammed, Lake Qarun and Wadi El Rayan. Fifteen have no coverage, including the El Qasr desert (4,055 km²), the Upper Nile (1,424 km²), El Qa plain, the Suez and Ain Sukhna coasts and Lake Idku.</div></div>
<p>The results match the KBA database for every KBA except two wetlands where the WDPA has only a Ramsar point: Lake Bardawil and Zaranik (51.6% here, 19.6% in the database) and Lake Burullus (89.4% against 83.5%). The KBA database doesn't buffer points; the indicator method does. Three foreign KBAs touch Egyptian jurisdiction: Tiran island (Saudi Arabia, 62 km²) and two Israeli sites along the border; they are listed in <code>kba_foreign_overlapping_EGY.csv</code> and not counted.</p>

{head(7, "Governance", "Sheet: Governance")}
{gov_mock}
<div class="result"><div><strong>Finding.</strong> Every site with a governance type is government-governed, but 12 sites report none, mainly El-Gelf El-Keber: <b>48%</b> of the covered land, and 46% of land and sea together, so the QC check fails its 5% threshold. Filling GOV_TYPE in the WDPA would clear it; it cannot be fixed in the tool.</div></div>

{head(8, "Management effectiveness", "Sheet: Mgmt_Effectiveness")}
<p>Twenty-eight site pages list GD-PAME evaluations: a RAPPAM assessment of most protectorates in 2006, METT assessments of St Katherine, El Omayed, Wadi El-Gemal–Hamata, Siwa and others (2009–2014), BREMi evaluations of the two biosphere reserves (2013) and World Heritage Outlooks for Wadi Al-Hitan up to 2025. The biosphere-reserve evaluations were moved to El Omayed and Wadi Al Alaqi, and the Wadi El Rayan Ramsar monitoring to the Wadi El Rayan protectorate, as recorded in column Y. The Wadi Al-Hitan evaluation stays on its own record, because the World Heritage site is only part of Wadi El Rayan.</p>
{pame_mock}
<p>Only Wadi Al-Hitan has a current evaluation, and it covers just 13 km² of net area. Everything else was last assessed between 2001 and 2014. Report this breakdown as provisional.</p>

{head(9, "Time series", "Sheet: Time_Series")}
{tschart()}
<p>Land coverage grew in two steps: the 1995–1996 designations of Elba, Wadi Al Alaqi, St Katherine and the Sinai coastal protectorates, and El-Gelf El-Keber National Park in 2007, which on its own added 5.3 points. Since then only El-Salum marine protected area (2010, 414 km²) and two small sites have been added. Marine coverage rose with Wadi El-Gemal–Hamata in 2003 and the Red Sea islands in 2006.</p>

{head(10, "Quality checks and reconciliation", "Sheet: QC_Checks")}
{qc_mock}
<div class="scroll"><table class="recon"><thead><tr><th></th><th>Land</th><th>Sea</th></tr></thead><tbody>
<tr><td>This workbook, Halaib excluded (land and sea)</td><td>110,805 of 986,014 km² = 11.24%</td><td>8,821 of 243,974 km² = 3.62%</td></tr>
<tr><td>This workbook, Halaib included (<code>07_sensitivity_halaib.py</code>)</td><td>128,668 of 1,004,056 km² = 12.81%</td><td>12,172 of 263,389 km² = 4.62%</td></tr>
<tr><td>Protected Planet, October 2026</td><td>128,943 of 982,592 km² = 13.12%</td><td>12,307 of 242,841 km² = 5.07%</td></tr>
<tr><td>NBSAP 2015–2030</td><td colspan="2">30 protected areas, about 149,000 km², "14.9% of the total land and marine areas"</td></tr>
</tbody></table></div>
<p>Protected Planet's protected areas (128,943 and 12,307 km²) match this workbook's figures <i>with</i> Halaib, while its land and sea totals match the base <i>without</i> Halaib. It appears to count Gebel Elba in full against a base map that excludes the triangle; the published figures can't confirm this. The national 14.9% counts land and sea together against the land area, and includes sites the WDPA lists as proposed. Explain these differences rather than mixing sources.</p>

{head(11, "Report", "Sheet: Dashboard")}
<blockquote class="draft">In 2026, protected areas covered 110,805 km², or 11.24% of Egypt's terrestrial and inland water area excluding the Halaib Triangle, and 8,821 km², or 3.62% of its marine and coastal area (Headline Indicator 3.1; WDPA October 2026; Mollweide equal-area); including Halaib, the figures are 12.81% and 4.62%. No OECMs have been reported. Reaching 30% would require a further 184,999 km² on land and 64,371 km² at sea; the national target of 20% would require about 86,000 km² more on land. On average, Egypt's Key Biodiversity Areas are 35.2% covered, and 15 of 33 have no coverage. The Nile valley and delta are almost unprotected. 48% of the covered land has no governance type reported, and no site apart from Wadi Al-Hitan has an effectiveness evaluation from the last five years.</blockquote>

{head(12, "What this example leaves out")}
<ol class="do">
<li><b>Halaib.</b> Excluded from the main figures to match Protected Planet's base map and the Marine Regions EEZ; the sensitivity script gives the alternative.</li>
<li><b>Proposed sites.</b> 13 protected areas proposed in 1999 (56,941 km²) are excluded until designated in the WDPA.</li>
<li><b>OECMs.</b> None reported; the NBSAP target explicitly counts them.</li>
<li><b>Marine biomes and effectiveness scores.</b> Bathymetry and assessment scores are not available here.</li>
</ol>

<h3>Sources</h3>
<ul class="sources">
<li>UNEP-WCMC &amp; IUCN (2026). <a href="https://www.protectedplanet.net/country/EGY">Protected Planet: Egypt</a>, WDPA/WD-OECM October 2026, and GD-PAME records on each site page.</li>
<li>GBF Indicators. <a href="https://www.gbf-indicators.org/metadata/headline/3-1">Metadata for Headline Indicator 3.1</a>.</li>
<li>BirdLife International on behalf of the KBA Partnership (2026). World Database of Key Biodiversity Areas, September 2026, and KBA trigger species.</li>
<li>Arab Republic of Egypt. National Biodiversity Strategy and Action Plan 2015–2030; updated NBSAP (2025); 5th National Report to the CBD.</li>
<li>Flanders Marine Institute (2023). EEZ v12. Runfola, D. et al. (2020). geoBoundaries (Egypt and Sudan ADM0). Snethlage, M.A. et al. (2022). GMBA Mountain Inventory v2.</li>
<li>Dinerstein, E. et al. (2017). BioScience 67(6): 534–545. Spalding, M.D. et al. (2007). BioScience 57(7): 573–583. Lehner, B. &amp; Grill, G. (2013). HydroRIVERS. Lehner, B. et al. (2025). GLWD v2. ESSD 17: 2277–2329.</li>
</ul>
<footer>Files: egypt/04_tool/GBF_3.1_Tool_Egypt_Worked_Example.xlsx (filled tool), with data, scripts, outputs and documents in the egypt folder. Workbook recalculated in Microsoft Excel with zero formula errors.</footer>
</main>
</div>
"""

page = f"""<title>Egypt Indicator 3.1 Walkthrough</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..800&family=IBM+Plex+Mono:wght@400;500&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">
<style>{CSS}</style>
{body}"""
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w").write(page)
print("written", OUT, len(page))
