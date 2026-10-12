"""Generate the illustrated Morocco walkthrough for the Indicator 3.1 tool (numbers from the Excel-recalculated workbook)."""
import csv, json, html, os
from shapely.geometry import shape, mapping

HERE = os.path.dirname(os.path.abspath(__file__))
OUTD = f"{HERE}/../outputs"
OUT = os.path.abspath(f"{HERE}/../../05_guide/Morocco_Indicator_3.1_Guide.html")
geo = json.load(open(f"{OUTD}/geom_moll_simplified.json"))
kgeo = json.load(open(f"{OUTD}/kba_geom_moll_simplified.json"))
cfg = json.load(open(f"{OUTD}/tool_config_morocco.json"))
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
R = dict(land=685174.25, sea=566672.87, pa_t=8849.406, oe_t=131066.069, tot_t=139915.475, pa_m=800.394, oe_m=118.113,
         cov_pa=0.012915555667, cov_oe=0.191288667663, cov_t=0.204204223329, cov_m=0.001620877601,
         gap_m=29.837912239856, need_m=169083.353)
# (year, land % with OECMs, land % PAs only, sea %)
ts = [(1940, 0, 0, 0), (1942, .0576, .0576, 0), (1944, .2475, .2475, 0), (1950, .2678, .2678, 0), (1980, .3137, .3137, .0057),
      (1991, .3637, .3637, .0280), (1994, 1.5076, .3638, .0422), (2004, 1.8998, .7560, .0852), (2005, 2.1044, .9606, .1335),
      (2006, 2.2953, 1.1515, .1494), (2008, 2.4174, 1.2736, .1494), (2019, 2.4353, 1.2916, .1555), (2021, 20.4204, 1.2916, .1621),
      (2026, 20.4204, 1.2916, .1621)]


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
sb = 200 * 1000 * k
scalebar = (f'<g font-size="11" fill="var(--ink-2)"><rect x="12" y="{H - 16}" width="{sb:.1f}" height="4" fill="var(--ink-2)"/>'
            f'<text x="{12 + sb + 6:.1f}" y="{H - 11}">200 km</text></g>')


def svgmap(inner, label):
    return f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{e(label)}">{base}{inner}{scalebar}</svg>'


def kcol(p):
    return "var(--accent)" if p >= 98 else "var(--kmid)" if p >= 50 else "var(--gap)" if p > 0 else "var(--kzero)"


kpaths = "".join(f'<path d="{path(kk["geom"])}" fill="{kcol(kk["pct"])}" fill-opacity="0.9" stroke="var(--ink)" stroke-width="0.4">'
                 f'<title>{e(kk["name"])}: {kk["pct"]:.1f}% covered</title></path>' for kk in sorted(kgeo["kba"], key=lambda kk: -kk["pct"]))
ghost = (f'<path d="{path(simp(geo["pa_t"], 1500))}" fill="none" stroke="var(--ink-2)" stroke-width="0.5" stroke-dasharray="2 2"/>'
         f'<path d="{path(simp(geo["oe_t"], 2500))}" fill="none" stroke="var(--oecm)" stroke-width="0.5" stroke-dasharray="2 2"/>')
legend = ('<ul class="legend"><li><i style="background:var(--nat)"></i>National PA</li><li><i style="background:var(--intl)"></i>International PA '
          '(Ramsar)</li><li><i style="background:var(--reg)"></i>Regional PA (SPAMI)</li><li><i style="background:var(--oecm)"></i>OECM (hunting reserve, SIBE)</li></ul>')
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


setup_rows = [(4, "Country / jurisdiction", "Morocco"), (5, "ISO3 code", "MAR"), (6, "Reporting year", "2026"),
              (7, "WDPA / WD-OECM release used", "WDPA/WD-OECM October 2026"), (8, "KBA dataset version", "World Database of KBAs, September 2026"),
              (9, "Base map used", "geoBoundaries ADM0 incl. Western Sahara + Moroccan EEZ and Western Sahara zone (EEZ v12), Mollweide"), (10, "Terrestrial area (km²)", "685,174.25"),
              (11, "Marine & coastal area (km²)", "566,672.87"), (12, "Target coverage", "30.0%"), (14, "PA layer flattened in GIS?", "Y"),
              (15, "OECM layer: PA overlap erased?", "Y"), (16, "Mollweide equal-area?", "Y"), (17, "Overlaps attributed to earliest site?", "Y"),
              (26, "PAME validity window (years)", "5"), (27, "Time-series start year", "1940")]
setup_mock = mock("Setup", [("A", "Parameter"), ("B", "Value")], [(r, [(l, "lab"), (v, "in")]) for r, l, v in setup_rows], " rows 4–27 (selection)")

sel = [4114, 101232, 15089, 555721499, 11697, 555781149, 29969, 555547509, 902713, 168216, 555698154, 555698150, 555721495, 555570055, 17710]
rowno = {r: 5 + i for i, r in enumerate(reg)}
reg_rows = []
for sid in sel:
    r = reg[sid]
    excl = "UNESCO-MAB Biosphere Reserve" if r[15] == "Y" else ("STATUS = Proposed" if r[7] == "Proposed" else "")
    reg_rows.append((rowno[sid], [(r[0], "in"), (r[1], "in"), (r[2], "in"), (r[4], "in"), (r[6], "in"), (r[7], "in"), (r[8], "in"),
                                  (f2(r[17], 1), "in"), (f2(r[18], 1), "in"), (r[21], "in"),
                                  (0 if excl else 1, "warn" if excl else "calc"), (excl, "warn" if excl else "calc")]))
reg_mock = mock("PA_OECM_Register", [("A", "SITE_ID"), ("B", "NAME"), ("C", "DESIG_ENG"), ("E", "Type"), ("G", "GOV_TYPE"), ("H", "STATUS"),
                                     ("I", "STATUS_YR"), ("R", "NET terr. km²"), ("S", "NET marine km²"), ("V", "PAME yr"),
                                     ("Z", "Included"), ("AA", "Exclusion reason")], reg_rows, " 15 of the 429 real rows, chosen to show each rule")

head_mock = mock("Headline_3.1", [("A", "Realm"), ("B", "Realm km²"), ("E", "PA used"), ("F", "OECM used"), ("H", "PA %"), ("I", "OECM %"),
                                  ("J", "Indicator 3.1"), ("L", "Gap (pp)"), ("M", "Extra km²"), ("N", "Status")],
                 [(6, [("Terrestrial & inland waters", "lab"), ("685,174.25", "calc"), ("8,849.41", "calc"), ("131,066.07", "calc"),
                       ("1.29%", "calc"), ("19.13%", "calc"), ("20.42%", "key"), ("9.6", "calc"), ("65,636.80", "calc"), ("Below target", "warn")]),
                  (7, [("Marine & coastal", "lab"), ("566,672.87", "calc"), ("800.39", "calc"), ("118.11", "calc"), ("0.14%", "calc"), ("0.02%", "calc"),
                       ("0.16%", "key"), ("29.8", "calc"), ("169,083.35", "calc"), ("Below target", "warn")])], " section A")

eco = list(csv.DictReader(open(f"{OUTD}/ecoregion_coverage.csv")))
meow = list(csv.DictReader(open(f"{OUTD}/marine_ecoregion_coverage.csv")))
eco_rows = []
for i, u in enumerate(sorted(eco, key=lambda x: -float(x["extent_km2"])) + sorted(meow, key=lambda x: -float(x["extent_km2"]))):
    ext, p, o = float(u["extent_km2"]), float(u["pa_km2"]), float(u["oecm_km2"])
    pct = (p + o) / ext
    eco_rows.append((58 + i, [(u.get("eco_name") or u["ecoregion"], "in"), (f2(ext, 0), "in"), (f2(p, 0), "in"), (f2(o, 0), "in"),
                              (f"{pct:.1%}", "key"), ("Yes" if pct >= 0.3 else "No", "pass" if pct >= 0.3 else "warn")]))
eco_mock = mock("Ecosystems", [("C", "Ecoregion"), ("F", "Extent km²"), ("G", "PA km²"), ("H", "OECM km²"), ("J", "Coverage"), ("K", "≥ 30%?")],
                eco_rows, " section D: 6 terrestrial and 3 marine ecoregions")
biome_mock = mock("Ecosystems", [("A", "GET"), ("C", "Biome / component"), ("F", "Extent"), ("G", "PA"), ("H", "OECM"), ("J", "Coverage")],
                  [(7, [("T2", "lab"), ("Temperate-boreal forests and woodlands", "lab"), ("10,980", "in"), ("2,106", "in"), ("1,556", "in"), ("33.4%", "key")]),
                   (8, [("T3", "lab"), ("Shrublands and shrub-dominated woodlands", "lab"), ("308,449", "in"), ("3,892", "in"), ("81,627", "in"), ("27.7%", "key")]),
                   (9, [("T4", "lab"), ("Savannas and grasslands (High Atlas steppe)", "lab"), ("6,347", "in"), ("533", "in"), ("1,369", "in"), ("29.97%", "key")]),
                   (10, [("T5", "lab"), ("Deserts and semi-deserts", "lab"), ("359,035", "in"), ("2,261", "in"), ("46,449", "in"), ("13.6%", "key")]),
                   (52, [("Rivers", "lab"), ("Rivers and streams (HydroRIVERS, km)", "lab"), ("164,971", "in"), ("2,373", "in"), ("32,813", "in"), ("21.3%", "key")]),
                   (53, [("Wetlands", "lab"), ("Lakes and wetlands (GLWD v2, km²)", "lab"), ("18,556", "in"), ("893", "in"), ("2,751", "in"), ("19.6%", "key")])],
                  " sections A and C")
wg = [x for x in csv.DictReader(open(f"{OUTD}/glwd_wetland_coverage_by_group.csv")) if x["counted"] == "Y" and float(x["extent_km2"]) >= 1]
wet_mock = mock("GLWD v2 · outputs/glwd_wetland_coverage_by_group.csv", [("", "Wetland group"), ("", "Extent km²"), ("", "PA km²"), ("", "OECM km²"), ("", "PA + OECM")],
                [(i + 1, [(x["group"], "lab"), (f2(float(x["extent_km2"]), 0), "calc"), (f2(float(x["pa_km2"]), 0), "calc"),
                          (f2(float(x["oecm_km2"]), 0), "calc"), (f'{float(x["pa_oecm_pct"]):.1f}%', "key")]) for i, x in enumerate(wg)]
                + [("Σ", [("Lakes and wetlands → Ecosystems row 53", "lab"), ("18,556", "calc"), ("893", "calc"), ("2,751", "calc"), ("19.6%", "key")])],
                " GIS output")

kba_by = {r[0]: r for r in cfg["kba"]}
krow = {r[0]: 16 + i for i, r in enumerate(cfg["kba"])}
kba_rows = []
for sid in [6509, 6495, 6503, 46603, 6515, 46645, 31683, 31856, 6487, 45664, 6521, 6520]:
    r = kba_by[sid]
    pa_p, all_p = min(1, r[7] / r[2]), min(1, (r[7] + r[8]) / r[2])
    cls = "Complete" if all_p >= 0.98 else ("Partial" if all_p > 0 else "None")
    kba_rows.append((krow[sid], [(r[0], "in"), (r[1], "in"), (f2(r[2], 1), "in"), (f2(r[3], 2), "in"), (r[5], "in"), (r[6], "in"),
                                 (f2(r[7], 1), "in"), (f2(r[8], 1), "in"), (f"{all_p:.1%}", "key"), (f"{pa_p:.1%}", "calc"),
                                 (cls, "pass" if cls == "Complete" else ("warn" if cls == "None" else "calc"))]))
kba_mock = mock("KBA_Coverage", [("A", "SitRecID"), ("B", "KBA name"), ("C", "Area km²"), ("D", "Ocean frac."), ("F", "Freshw."), ("G", "Mountain"),
                                 ("H", "PA km²"), ("I", "OECM km²"), ("L", "% PA+OECM"), ("M", "% PA only"), ("O", "Class")],
                kba_rows, " 12 of 73 rows, all values from the KBA polygons")
kba_sum = mock("KBA_Coverage", [("A", "KBA group"), ("B", "SDG"), ("C", "KBAs"), ("D", "Mean % PA+OECM"), ("E", "Mean % PA only"), ("G", "None"),
                                ("H", "Partial"), ("I", "Complete")],
               [(6, [("All KBAs", "lab"), ("—", "calc"), ("73", "calc"), ("53.7%", "key"), ("22.2%", "calc"), ("10", "calc"), ("45", "calc"), ("18", "calc")]),
                (7, [("Terrestrial KBAs", "lab"), ("15.1.2", "calc"), ("67", "calc"), ("57.0%", "key"), ("22.7%", "calc"), ("6", "calc"), ("44", "calc"), ("17", "calc")]),
                (8, [("Freshwater KBAs", "lab"), ("15.1.2", "calc"), ("38", "calc"), ("54.5%", "key"), ("26.3%", "calc"), ("2", "calc"), ("28", "calc"), ("8", "calc")]),
                (9, [("Marine KBAs (≥5% ocean)", "lab"), ("14.5.1", "calc"), ("21", "calc"), ("53.2%", "key"), ("32.4%", "calc"), ("6", "calc"), ("12", "calc"), ("3", "calc")]),
                (10, [("Mountain KBAs", "lab"), ("15.4.1", "calc"), ("32", "calc"), ("48.3%", "key"), ("19.5%", "calc"), ("0", "calc"), ("27", "calc"), ("5", "calc")])],
               " section A (results)")

gov_mock = mock("Governance", [("A", "IUCN governance type"), ("B", "Sites"), ("C", "Terr. PA km²"), ("D", "Terr. OECM km²"), ("G", "% of covered land")],
                [(6, [("A. Governance by government", "lab"), ("163", "calc"), ("8,849.41", "calc"), ("7,836.83", "calc"), ("11.9%", "key")]),
                 (7, [("B. Shared governance (hunting reserves)", "lab"), ("221", "calc"), ("0", "calc"), ("123,229.24", "calc"), ("88.1%", "key")]),
                 (8, [("C. Private governance", "lab"), ("0", "calc"), ("0", "calc"), ("0", "calc"), ("0.0%", "calc")]),
                 (9, [("D. Indigenous peoples & local communities", "lab"), ("0", "calc"), ("0", "calc"), ("0", "calc"), ("0.0%", "calc")]),
                 (10, [("Not reported", "lab"), ("0", "calc"), ("0", "calc"), ("0", "calc"), ("0.0%", "calc")]),
                 (11, [("TOTAL", "lab"), ("384", "calc"), ("8,849.41", "calc"), ("131,066.07", "calc"), ("100%", "calc")])], " section A")

pame_mock = mock("Mgmt_Effectiveness", [("A", "Effectiveness class"), ("B", "Sites"), ("C", "Terr. PA km²"), ("D", "Terr. OECM km²"), ("G", "% of covered land"), ("J", "Marine km²")],
                 [(6, [("High / Moderate / Low (scored)", "lab"), ("0", "calc"), ("0", "calc"), ("0", "calc"), ("0.0%", "calc"), ("0", "calc")]),
                  (9, [("Assessed – no score (current)", "lab"), ("0", "calc"), ("0", "calc"), ("0", "calc"), ("0.0%", "warn"), ("0", "calc")]),
                  (10, [("Assessment outdated (2001–2018)", "lab"), ("10", "calc"), ("3,290.41", "warn"), ("2.55", "warn"), ("2.4%", "warn"), ("515.46", "warn")]),
                  (11, [("Not assessed", "lab"), ("374", "calc"), ("5,559.00", "calc"), ("131,063.52", "calc"), ("97.6%", "calc"), ("403.05", "calc")])], " section A (selection)")

qc = [("Realm areas entered", "Both", "PASS"), ("PA layer flattened", "Y", "PASS"), ("OECMs: PA overlap erased", "Y", "PASS"),
      ("Mollweide projection", "Y", "PASS"), ("Included sites without flattened net area", "0", "PASS"), ("Terrestrial coverage ≤ 100%", "20.42%", "PASS"),
      ("Marine coverage ≤ 100%", "0.16%", "PASS"), ("Included sites with any QC flag", "63", "WARN"), ("Included sites with STATUS_YR missing", "0", "PASS"),
      ("Share of area with GOV_TYPE not reported", "0.0%", "PASS"), ("Governance total = headline total", "0.000", "PASS"),
      ("KBAs with covered area > KBA area", "0", "PASS"), ("Example (fictional) data present", "0", "PASS")]
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
    rows = [("PAs: sum of site areas", 9447, "var(--gap)"), ("PAs: after flattening", 8849, "var(--accent)"),
            ("OECMs: sum of site areas", 143892, "var(--gap)"), ("OECMs: PA area removed", 131066, "var(--oecm)")]
    sx = lambda v: 210 + v / 150000 * (w - 300)
    out = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Gross versus flattened area for PAs and OECMs on land" class="chart">']
    for i, (lab, v, c) in enumerate(rows):
        y = 6 + i * 36
        out.append(f'<text x="200" y="{y + 17}" text-anchor="end" class="lab">{lab}</text><rect x="210" y="{y}" width="{max(2, sx(v) - 210):.1f}" height="24" rx="2" fill="{c}"/>'
                   f'<text x="{sx(v) + 6:.1f}" y="{y + 17}" class="val">{v:,.0f} km²</text>')
    return "".join(out) + "</svg>"


def tschart():
    w, h, l, r, t, b = 560, 250, 44, 16, 16, 30
    sx = lambda y: l + (y - 1940) / (2030 - 1940) * (w - l - r)
    sy = lambda v: t + (1 - v / 40) * (h - t - b)
    grid = "".join(f'<line x1="{l}" x2="{w - r}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" stroke="var(--line)"/><text x="{l - 6}" y="{sy(v) + 4:.1f}" text-anchor="end">{v}%</text>' for v in (0, 10, 20, 30, 40))
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
<text x="{sx(2026) - 6:.1f}" y="{sy(20.42) - 8:.1f}" text-anchor="end" class="val" style="fill:var(--oecm)">land, PA+OECM 20.4%</text>
<text x="{sx(2026) - 6:.1f}" y="{sy(1.29) - 8:.1f}" text-anchor="end" class="val" style="fill:var(--accent)">land, PA only 1.29%</text>
<text x="{sx(2026) - 6:.1f}" y="{sy(0.16) + 14:.1f}" text-anchor="end" class="val" style="fill:var(--intl)">sea 0.16%</text>
<text x="{sx(1994) - 4:.1f}" y="{sy(2.49) - 22:.1f}" text-anchor="end" class="lab">1994: SIBEs</text>
<text x="{sx(2021) - 4:.1f}" y="{sy(20) :.1f}" text-anchor="end" class="lab">2021: 221 hunting reserves</text></svg>'''


steps = [("data", "Collect the data"), ("setup", "Fill in Setup: Morocco including Western Sahara"), ("gis", "Flatten PAs and OECMs in GIS"),
         ("register", "Enter the site register"), ("headline", "Read the headline"), ("oecm", "The OECM question"), ("eco", "Ecosystems and inland waters"),
         ("kba", "Key Biodiversity Areas"), ("gov", "Governance"), ("pame", "Management effectiveness"), ("ts", "Time series"),
         ("qc", "Quality checks and reconciliation"), ("report", "Report"), ("gaps", "What this example leaves out")]
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
<h1>Morocco including Western Sahara, step by step through the 30×30 tool</h1>
<p class="lede">This guide fills the Indicator 3.1 Excel tool for Morocco from the 429 records in the October 2026 World Database on Protected Areas and World Database on OECMs, the 73 official Key Biodiversity Area polygons and points (September 2026), and a GIS run over land and sea. <b>This version counts Morocco including Western Sahara</b>: the land and sea south of 27°40′N are in the denominators, and the six KBAs there are counted. Every number comes from those data and from the workbook recalculated in Excel.</p>
<p>Morocco shows two things the tool has to handle carefully. Most of its covered land is in 338 OECMs, chiefly permanent hunting reserves under shared governance, while protected areas alone cover about 1.3%. And the denominator depends on how Western Sahara is treated: here it is included, which adds 269,939 km² of land and 285,374 km² of sea but no protected area or OECM.</p>
<div class="facts six">
<div><b>429</b><small>records: 91 PA polygons, 338 OECMs</small></div>
<div><b>1.29%</b><small>of land in protected areas</small></div>
<div><b>19.13%</b><small>of land added by OECMs</small></div>
<div><b>20.42%</b><small>land coverage, PAs + OECMs (65,637 km² short of 30%)</small></div>
<div><b>0.16%</b><small>of 566,673 km² of sea</small></div>
<div><b>169,083 km²</b><small>of sea still needed for 30%</small></div>
</div>
</header>

{head(0, "Collect the data")}
<p>Everything used here is in the <code>morocco_incl_western_sahara/01_data</code> folder:</p>
<ol class="do">
<li><b>Protected areas and OECMs.</b> WDPA and WD-OECM, October 2026, from the UNEP-WCMC map service behind <a href="https://www.protectedplanet.net/country/MAR">Protected Planet</a>: 91 protected-area polygons (42 of them still <i>Proposed</i>) and 338 OECM polygons, as shapefile, GeoJSON and GeoPackage. There are no point sites.</li>
<li><b>Base map.</b> Land: the full geoBoundaries ADM0 outline, including Western Sahara (see Step 2). Sea: the Marine Regions EEZ v12 "Moroccan Exclusive Economic Zone" plus the "Overlapping claim Western Sahara" zone, with coastal gaps closed (199 km²).</li>
<li><b>Key Biodiversity Areas.</b> The World Database of KBAs, September 2026: 70 polygons (including the six south of 27°40′N) and 3 points with a reported area, which are buffered into circles like WDPA points; 424 trigger-species records. Licensed data; don't republish the polygons.</li>
<li><b>Management effectiveness.</b> GD-PAME evaluations on the 429 site pages: 11 sites carry at least one.</li>
<li><b>Ecosystems, mountains and inland waters.</b> RESOLVE Ecoregions 2017, Marine Ecoregions of the World, GMBA v2.0, HydroRIVERS and GLWD v2, clipped by <code>00_prepare_layers.py</code>.</li>
</ol>

{head(1, "Fill in Setup and the Western Sahara question", "Sheet: Setup")}
<p>This version follows Morocco's national position and counts Western Sahara as part of Morocco. The geoBoundaries outline for Morocco already includes it. Protected Planet, the Marine Regions EEZ and the WDPA keep it separate: Protected Planet's land area for Morocco is 414,105 km², the "Moroccan EEZ" stops at 27°40′N, and Western Sahara's waters are a separate "overlapping claim" zone. Neither the WDPA nor the WD-OECM has any record in Western Sahara, under Morocco's code or under its own (ESH).</p>
<p>So the land area is the full outline, 685,174 km² (415,235 km² north of 27°40′N plus 269,939 km² south of it), and the sea is the Moroccan EEZ plus the Western Sahara zone, 566,673 km² (281,295 + 285,374, with coastal gaps). The six KBAs south of the line (the Dakhla area, Baie d'Ad Dakhla, Pointe d'Awfist, the Laâyoune wetland and two Canary Current offshore sites) are counted, giving 73. The protected and OECM area hardly changes: only 0.28 km² of Khnifiss National Park lies south of the line. So the coverage falls: land from 33.70% to 20.42%, sea from 0.33% to 0.16%. The version without Western Sahara, which matches Protected Planet, is in the <code>morocco</code> folder. Whatever choice a country makes, state it in Setup row 9 and use the same base map for every number.</p>
{setup_mock}
{cellkey}

{head(2, "Flatten PAs and OECMs in GIS", "Outside Excel: 03_analysis/scripts/01_gis_flatten.py")}
<p>Protected areas are dissolved into one flat layer; OECMs are measured only where no protected area lies. With 338 OECMs this step matters: the hunting reserves overlap the national parks and the SIBEs, in 216 overlapping pairs.</p>
<div class="maps">
<figure><figcaption><b>Before: 384 records</b>Stacked records over the same ground</figcaption>{svgmap(before, "Protected-area and OECM records in Morocco")}{legend}</figure>
<figure><figcaption><b>After: PAs, then OECMs</b>8,849 km² of PAs and 131,066 km² of OECMs on land, each counted once</figcaption>{svgmap(flat, "Flattened PA and OECM layers in Morocco")}{legend2}</figure>
</div>
{bars()}
<h3>The procedure (metadata steps 1–6)</h3>
<ol class="do">
<li><b>Filter.</b> 45 records drop out: 42 with status <i>Proposed</i> (the seven new natural parks, among them Jbel Krouz, Plateau Central and Bouhachem; Draa-Warkziz-Lebtana National Park; five marine protected areas including Mogador, Alboran, Massa and Agadir; the Essaouira archipelago nature reserve; and 28 biological reserves: 11,064 km² in all), and 3 UNESCO biosphere reserves (Arganeraie, Oasis du Sud Marocain, Cédraie de l'Atlas).</li>
<li><b>Clip and project.</b> Each site is split into land and sea parts and measured in Mollweide.</li>
<li><b>Dissolve PAs.</b> 9,447 km² summed becomes <b>8,849 km²</b> on land (8,849.41 km², 0.28 km² more than without Western Sahara); at sea, 1,055 km² becomes <b>800 km²</b>.</li>
<li><b>Erase PAs from OECMs, then dissolve.</b> The OECMs sum to 143,892 km² on land. Removing the protected areas inside them, mainly the national parks of Ifrane (1,195 km²), Iriqui (825 km²) and Khénifra (772 km²), each also listed as a hunting reserve, and removing overlaps between hunting reserves and SIBEs, leaves <b>131,066 km²</b>.</li>
<li><b>Attribute overlaps.</b> Protected areas first, then OECMs, earliest designation first. The 1994 SIBEs therefore keep their area and the 2021 hunting reserves get what is left.</li>
</ol>

{head(3, "Enter the site register", "Sheet: PA_OECM_Register")}
<p>All 429 records go in. Column E separates protected areas from OECMs and column G carries the governance type, which matters here: every hunting reserve is reported as collaborative governance.</p>
{reg_mock}

{head(4, "Read the headline", "Sheet: Headline_3.1")}
{head_mock}
{gauge([(1.2916, "var(--accent)"), (19.1289, "var(--oecm)")], "Land", "protected areas 1.29% + OECMs 19.13% = 20.42%")}
{gauge([(0.1412, "var(--intl)"), (0.0208, "var(--oecm)")], "Sea", "gap 29.8 points = 169,083 km²")}
<div class="result"><div><strong>Result.</strong> PAs and OECMs cover <b>20.42%</b> of Morocco's land including Western Sahara, so the land element of Target 3 is not met: another <b>65,637 km²</b> (9.6 points) is needed. They cover <b>0.16%</b> of its waters (918 km² of 566,673 km²); reaching 30% at sea would take another <b>169,083 km²</b>. The five proposed marine protected areas, Mogador, Alboran, Massa, Agadir and Souss-Massa, would add roughly 1,500 km² once designated.</div></div>

{head(5, "The OECM question")}
<p>Without the OECMs, Morocco's land coverage would be 1.29%. The 221 permanent hunting reserves, all reported in 2021, provide 123,267 km², or 18.0 points; the 117 SIBEs provide 7,918 km².</p>
<div class="pitfall"><h3>What to check before reporting</h3>
<p>An OECM must deliver positive, long-term outcomes for biodiversity, whatever its main purpose (CBD decision 14/8). Hunting reserves are managed for game, and their biodiversity outcomes need to be documented. None of the 221 has a management-effectiveness evaluation in GD-PAME. State the evidence for their OECM status in the report, and give the PA and OECM figures separately.</p></div>

{head(6, "Ecosystems and inland waters", "Sheet: Ecosystems")}
{eco_mock}
{biome_mock}
<p>The High Atlas juniper steppe (biome T4) reaches 29.97%, a hair under the line, so the tool marks it "No". Only one of the four biomes reaches 30%: temperate forests (33.4%). Deserts fall from 53.4% to 13.6%, because Western Sahara adds 268,000 km² of desert with no protected area or OECM: the Saharan Atlantic coastal desert (22,772 km²), the South Sahara desert (96,373 km²), the Saharan halophytics (360 km²) and 148,000 km² more of North Saharan steppe, all at 0%.</p>
{wet_mock}
<div class="result"><div><strong>Finding.</strong> The Mediterranean woodlands and forests, Morocco's largest ecoregion (145,990 km²), are 14.9% covered, and the argan woodlands 20.3%. Inland waters are poorly covered: 19.6% of lakes and wetlands, with marshes at 13% and riverine wetlands at 17%, and 21.3% of river length. At sea, the Saharan Upwelling ecoregion, 519,000 km² of Morocco's waters including Western Sahara's, is 0.07% covered.</div></div>

{head(7, "Key Biodiversity Areas", "Sheet: KBA_Coverage · script 02_kba_overlay.py")}
<div class="maps one"><figure><figcaption><b>73 KBAs by share covered (PAs + OECMs)</b>Official KBA polygons and buffered points, September 2026</figcaption>{svgmap(ghost + kpaths, "Key Biodiversity Areas of Morocco coloured by covered share")}{klegend}</figure></div>
{kba_mock}
{kba_sum}
<div class="result"><div><strong>Finding.</strong> On average, Moroccan KBAs are <b>53.7%</b> covered, but only 22.2% by protected areas; the OECMs more than double the figure. Ten KBAs have no coverage at all, six of them the KBAs of Western Sahara. The largest uncovered KBA areas are the Dakhla area (18,980 km²), the Canary Current shelf-break (north) (11,008 km²), the Canary Current shelf sites 1, 2 and 3 (13,321 km² together), Wad Lakhdar (2,911 km²) and Msseyed (2,477 km²).</div></div>
<p>The PA-only results match the KBA database's figures for every KBA it reports (the KBA database gives no figure for the six Western Sahara sites), which confirms the protected-area layer. Four foreign KBAs overlap Morocco's land or waters: two Algerian sites by 3–4 km² along the border, and two Spanish sites, the Strait of Gibraltar (37 km²) and the Chafarinas Islands (275 km²), whose waters lie inside the Moroccan EEZ as drawn by Marine Regions. They are listed in <code>kba_foreign_overlapping_MAR.csv</code> and not counted.</p>

{head(8, "Governance", "Sheet: Governance")}
{gov_mock}
<div class="result"><div><strong>Finding.</strong> Unusually, most of the covered land, 88.1%, is under <b>shared governance</b>: all 221 hunting reserves are reported in the WD-OECM with GOV_TYPE "Collaborative governance". Who shares that governance is not recorded; document it in the report. Protected areas and SIBEs are all government-governed. No site is governed by Indigenous peoples or local communities, and every site reports a governance type, so the QC check passes.</div></div>

{head(9, "Management effectiveness", "Sheet: Mgmt_Effectiveness")}
<p>Eleven site pages list GD-PAME evaluations: METT assessments of Toubkal and Ifrane (2013), Talassemtane (2005) and Sebkha Bou Areg (2014), IMET assessments of Tazekka and Al Hoceima (2018), BirdLife IBA monitoring (2001) and a BREMi evaluation of the Oasis du Sud Marocain biosphere reserve (2013). The Al Hoceima evaluation sits on the SPAMI record and was moved to Al Hoceima National Park, which holds the area; the biosphere-reserve evaluation stays on its excluded record.</p>
{pame_mock}
<p>No evaluation is less than five years old, so no covered area has a current effectiveness assessment. The ten evaluated sites cover 2.4% of the covered land and 56% of the covered sea.</p>

{head(10, "Time series", "Sheet: Time_Series")}
{tschart()}
<p>Protected-area coverage has grown slowly since Toubkal National Park in 1942, reaching 1.29% in 2019. The SIBEs added 1.1 points in 1994. Then, in 2021, the 221 hunting reserves added 18.0 points in a single year. At sea, coverage has never exceeded 0.16%.</p>

{head(11, "Quality checks and reconciliation", "Sheet: QC_Checks")}
{qc_mock}
<p>The one warning covers 63 flagged sites, mostly realm mismatches between the WDPA field and the GIS split along the coast. Review them, but they don't change the headline.</p>
<div class="scroll"><table class="recon"><thead><tr><th></th><th>PA land</th><th>PA + OECM land</th><th>Sea (PA + OECM)</th></tr></thead><tbody>
<tr><td>This workbook (geoBoundaries incl. Western Sahara + Moroccan EEZ and Western Sahara zone)</td><td>8,849 of 685,174 km² = 1.29%</td><td>139,915 km² = 20.42%</td><td>919 of 566,673 km² = 0.16%</td></tr>
<tr><td>Same data without Western Sahara (<code>morocco</code> folder)</td><td>8,849 of 415,235 km² = 2.13%</td><td>139,915 km² = 33.70%</td><td>919 of 281,295 km² = 0.33%</td></tr>
<tr><td>Protected Planet, October 2026</td><td>8,863 of 414,105 km² = 2.14%</td><td>139,767 km² = 33.75%</td><td>873 of 280,342 km² = 0.31%</td></tr>
<tr><td>Morocco's 7th National Report (2026), indicator 3.1</td><td colspan="2">24.2% (2025, national data set), ambition 30% by 2030</td><td>–</td></tr>
<tr><td>Morocco's 6th National Report (as cited by Protected Planet)</td><td colspan="2">16.2%</td><td>–</td></tr>
</tbody></table></div>
<p>The covered areas match Protected Planet's within about 0.1%; the percentages differ only because Protected Planet's denominators leave Western Sahara out. Without it, the workbook and Protected Planet agree within 0.05 points. The national figure of 24.2% uses national data, and the report lists a protected-area network of 12,787 km², including 5,067 km² of new natural parks that the WDPA still records as <i>Proposed</i>. Updating their status in the WDPA would bring the protected-area figure to about 2.0% (about 3.4% without Western Sahara). The report doesn't say how OECMs enter its 24.2%; explain the difference rather than mixing sources.</p>

{head(12, "Report", "Sheet: Dashboard")}
<blockquote class="draft">In 2026, protected areas covered 8,849 km², or 1.29% of Morocco's terrestrial and inland water area (including Western Sahara), and other effective area-based conservation measures a further 131,066 km², or 19.13%, mostly permanent hunting reserves under shared governance; together 20.42% (Headline Indicator 3.1; WDPA/WD-OECM October 2026; Mollweide equal-area); reaching 30% would require a further 65,637 km². Marine and coastal coverage was 919 km², or 0.16%; reaching 30% would require a further 169,083 km². On average, Morocco's 73 Key Biodiversity Areas are 53.7% covered, 22.2% by protected areas alone. Coverage ranges from 0% of the Saharan Atlantic coastal desert and the South Sahara desert to 67.8% of Mediterranean dry woodlands and steppe. 88% of the covered land is under shared governance; no covered area has a management-effectiveness evaluation from the last five years.</blockquote>

{head(13, "What this example leaves out")}
<ol class="do">
<li><b>Western Sahara.</b> Included in land, sea and KBAs, so the percentages differ from Protected Planet's. The WDPA has no site there; any national protected area south of 27°40′N must be reported to the WDPA before it can be counted.</li>
<li><b>The OECM evidence.</b> The tool counts the hunting reserves and SIBEs as reported; checking them against CBD 14/8 is a national task.</li>
<li><b>Proposed sites.</b> 42 proposed protected areas, 11,064 km², are excluded until their status changes in the WDPA.</li>
<li><b>Marine biomes and effectiveness scores.</b> Shelf versus pelagic waters need bathymetry; GD-PAME gives no scores.</li>
</ol>

<h3>Sources</h3>
<ul class="sources">
<li>UNEP-WCMC &amp; IUCN (2026). <a href="https://www.protectedplanet.net/country/MAR">Protected Planet: Morocco</a>, WDPA/WD-OECM October 2026, and GD-PAME records on each site page.</li>
<li>GBF Indicators. <a href="https://www.gbf-indicators.org/metadata/headline/3-1">Metadata for Headline Indicator 3.1</a>. CBD decision 14/8 on OECMs.</li>
<li>BirdLife International on behalf of the KBA Partnership (2026). World Database of Key Biodiversity Areas, September 2026, and KBA trigger species.</li>
<li>Royaume du Maroc (2026). 7th National Report to the CBD; 5th and 4th National Reports; national biodiversity strategy.</li>
<li>Flanders Marine Institute (2023). EEZ v12. Runfola, D. et al. (2020). geoBoundaries. Snethlage, M.A. et al. (2022). GMBA Mountain Inventory v2.</li>
<li>Dinerstein, E. et al. (2017). BioScience 67(6): 534–545. Spalding, M.D. et al. (2007). BioScience 57(7): 573–583. Lehner, B. &amp; Grill, G. (2013). HydroRIVERS. Lehner, B. et al. (2025). GLWD v2. ESSD 17: 2277–2329.</li>
</ul>
<footer>Files: morocco/04_tool/GBF_3.1_Tool_Morocco_Worked_Example.xlsx (filled tool), with data, scripts, outputs and documents in the morocco folder. Workbook recalculated in Microsoft Excel with zero formula errors.</footer>
</main>
</div>
"""

page = f"""<title>Morocco (incl. Western Sahara) Indicator 3.1</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..800&family=IBM+Plex+Mono:wght@400;500&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">
<style>{CSS}</style>
{body}"""
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w").write(page)
print("written", OUT, len(page))
