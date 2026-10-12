"""Build the GBF Headline Indicator 3.1 national calculation workbook."""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.comments import Comment
from openpyxl.utils import get_column_letter as CL

import os, json
OUT = "/Users/zakherfrogman/Documents/Tool for 30x30/GBF_Indicator_3.1_National_Tool.xlsx"
CFG = json.load(open(os.environ["TOOL_CFG"])) if os.environ.get("TOOL_CFG") else None
if CFG:
    OUT = CFG["out"]

# ---------------------------------------------------------------- styles
F = "Arial"
f_base = Font(name=F, size=10)
f_bold = Font(name=F, size=10, bold=True)
f_title = Font(name=F, size=16, bold=True, color="1F4E3D")
f_sub = Font(name=F, size=11, bold=True, color="1F4E3D")
f_hdr = Font(name=F, size=10, bold=True, color="FFFFFF")
f_in = Font(name=F, size=10, color="0000FF")
f_note = Font(name=F, size=9, italic=True, color="595959")
f_link = Font(name=F, size=10, color="008000")
fill_hdr = PatternFill("solid", fgColor="1F4E3D")
fill_sec = PatternFill("solid", fgColor="D9EAD3")
fill_in = PatternFill("solid", fgColor="FFF2CC")
fill_calc = PatternFill("solid", fgColor="F2F2F2")
fill_key = PatternFill("solid", fgColor="DDEBF7")
fill_ex = PatternFill("solid", fgColor="FCE4D6")
thin = Side(style="thin", color="BFBFBF")
bord = Border(left=thin, right=thin, top=thin, bottom=thin)
wrap = Alignment(wrap_text=True, vertical="top")
center = Alignment(horizontal="center", vertical="center", wrap_text=True)
PCT = "0.0%"
KM2 = "#,##0.0"

wb = Workbook()


def sheet(name, tab=None):
    ws = wb.create_sheet(name)
    ws.sheet_view.showGridLines = False
    if tab:
        ws.sheet_properties.tabColor = tab
    return ws


def title(ws, text, subtitle=None):
    ws["A1"] = text
    ws["A1"].font = f_title
    if subtitle:
        ws["A2"] = subtitle
        ws["A2"].font = f_note


def header(ws, row, col, labels, height=45):
    for i, lab in enumerate(labels):
        c = ws.cell(row=row, column=col + i, value=lab)
        c.font, c.fill, c.alignment, c.border = f_hdr, fill_hdr, center, bord
    ws.row_dimensions[row].height = height


def put(ws, ref, value, kind="calc", fmt=None, bold=False):
    c = ws[ref]
    c.value = value
    c.border = bord
    if kind == "in":
        c.font, c.fill = f_in, fill_in
    elif kind == "calc":
        c.font, c.fill = (f_bold if bold else f_base), fill_calc
    elif kind == "key":
        c.font, c.fill = Font(name=F, size=11, bold=True), fill_key
    elif kind == "label":
        c.font = f_bold if bold else f_base
        c.alignment = wrap
    elif kind == "link":
        c.font, c.fill = f_link, fill_calc
    if fmt:
        c.number_format = fmt
    return c


def widths(ws, d):
    for k, v in d.items():
        ws.column_dimensions[k].width = v


def section(ws, row, text, ncols=8):
    for col in range(1, ncols + 1):
        ws.cell(row=row, column=col).fill = fill_sec
    c = ws.cell(row=row, column=1, value=text)
    c.font = f_sub


def note(ws, ref, text):
    ws[ref] = text
    ws[ref].font = f_note
    ws[ref].alignment = Alignment(wrap_text=False, vertical="top")


# ================================================================ LISTS
L = wb.active
L.title = "Lists"
L.sheet_properties.tabColor = "808080"
lists = {
    "A": ("Site type", ["PA", "OECM"]),
    "B": ("IUCN_CAT", ["Ia", "Ib", "II", "III", "IV", "V", "VI", "Not Reported", "Not Applicable", "Not Assigned"]),
    "C": ("STATUS", ["Designated", "Inscribed", "Adopted", "Established", "Proposed", "Not Reported"]),
    "F": ("MARINE", [0, 1, 2]),
    "G": ("Geometry", ["Polygon", "Point"]),
    "H": ("Y/N", ["Y", "N"]),
    "I": ("DESIG_TYPE", ["National", "Regional", "International", "Not Applicable"]),
    "J": ("PAME class", ["High", "Moderate", "Low", "Assessed – no score", "Assessment outdated", "Not assessed"]),
    "K": ("PAME tool", ["METT", "METT-4", "RAPPAM", "IMET", "Enhancing our Heritage (EoH)", "Management Effectiveness Evaluation (MEE)",
                        "R-METT (Ramsar)", "IUCN Green List assessment", "SAGE (governance & equity)", "National methodology", "Other"]),
    "L": ("Ecosystem unit level", ["GET Ecosystem Functional Group", "Terrestrial ecoregion (Dinerstein et al. 2017)",
                                   "Freshwater ecoregion (Abell et al. 2008)", "Marine ecoregion (Spalding et al. 2007)",
                                   "Pelagic province (Spalding et al. 2012)", "National ecosystem type"]),
}
gov = [
    ("Federal or national ministry or agency", "A. Governance by government"),
    ("Sub-national ministry or agency", "A. Governance by government"),
    ("Government-delegated management", "A. Governance by government"),
    ("Transboundary governance", "B. Shared governance"),
    ("Collaborative governance", "B. Shared governance"),
    ("Joint governance", "B. Shared governance"),
    ("Individual landowners", "C. Private governance"),
    ("Non-profit organisations", "C. Private governance"),
    ("For-profit organisations", "C. Private governance"),
    ("Indigenous peoples", "D. Governance by Indigenous peoples and local communities"),
    ("Local communities", "D. Governance by Indigenous peoples and local communities"),
    ("Not Reported", "Not reported"),
]
gov_groups = ["A. Governance by government", "B. Shared governance", "C. Private governance",
              "D. Governance by Indigenous peoples and local communities", "Not reported"]
# IUCN Global Ecosystem Typology v2 – 25 biomes (Keith et al. 2022)
biomes = [
    ("T1", "Terrestrial", "Tropical-subtropical forests", "Y", "km²"),
    ("T2", "Terrestrial", "Temperate-boreal forests and woodlands", "Y", "km²"),
    ("T3", "Terrestrial", "Shrublands and shrub-dominated woodlands", "Y", "km²"),
    ("T4", "Terrestrial", "Savannas and grasslands", "Y", "km²"),
    ("T5", "Terrestrial", "Deserts and semi-deserts", "Y", "km²"),
    ("T6", "Terrestrial", "Polar/alpine (cryogenic)", "Y", "km²"),
    ("T7", "Terrestrial", "Intensive land-use systems", "N", "km²"),
    ("S1", "Subterranean", "Subterranean lithic systems", "N", "km²"),
    ("S2", "Subterranean", "Anthropogenic subterranean voids", "N", "km²"),
    ("SF1", "Subterranean-freshwater", "Subterranean freshwaters", "N", "km²"),
    ("SF2", "Subterranean-freshwater", "Anthropogenic subterranean freshwaters", "N", "km²"),
    ("SM1", "Subterranean-marine", "Subterranean tidal systems", "N", "km²"),
    ("TF1", "Freshwater-terrestrial", "Palustrine wetlands", "Y", "km²"),
    ("F1", "Freshwater", "Rivers and streams", "Y", "km (length)"),
    ("F2", "Freshwater", "Lakes", "Y", "km²"),
    ("F3", "Freshwater", "Artificial wetlands", "N", "km²"),
    ("FM1", "Freshwater-marine", "Semi-confined transitional waters", "Y", "km²"),
    ("M1", "Marine", "Marine shelf", "Y", "km²"),
    ("M2", "Marine", "Pelagic ocean waters", "Y", "km²"),
    ("M3", "Marine", "Deep sea floors", "Y", "km²"),
    ("M4", "Marine", "Anthropogenic marine systems", "N", "km²"),
    ("MT1", "Marine-terrestrial", "Shorelines", "Y", "km²"),
    ("MT2", "Marine-terrestrial", "Supralittoral coastal systems", "Y", "km²"),
    ("MT3", "Marine-terrestrial", "Anthropogenic shorelines", "N", "km²"),
    ("MFT1", "Marine-freshwater-terrestrial", "Brackish tidal systems", "Y", "km²"),
]
L["A1"] = "Drop-down lists and lookup tables (do not edit unless the WDPA schema changes)"
L["A1"].font = f_sub
LR = {}  # name -> absolute range
for col, (hd, vals) in lists.items():
    L[f"{col}3"] = hd
    L[f"{col}3"].font = f_bold
    for i, v in enumerate(vals):
        L[f"{col}{4 + i}"] = v
    LR[hd] = f"Lists!${col}$4:${col}${3 + len(vals)}"
L["D3"], L["E3"] = "GOV_TYPE (WDPA)", "IUCN governance type"
L["D3"].font = L["E3"].font = f_bold
for i, (g, grp) in enumerate(gov):
    L[f"D{4 + i}"], L[f"E{4 + i}"] = g, grp
GOV_RANGE = f"Lists!$D$4:$D${3 + len(gov)}"
GOV_TABLE = f"Lists!$D$4:$E${3 + len(gov)}"
L["M3"] = "GET biome code"
L["M3"].font = f_bold
for i, b in enumerate(biomes):
    L[f"M{4 + i}"] = b[0]
BIOME_RANGE = f"Lists!$M$4:$M${3 + len(biomes)}"
widths(L, {c: 30 for c in "ABCDEFGHIJKLM"})
L.column_dimensions["D"].width = 40
L.column_dimensions["E"].width = 52


def dv_list(ws, rng_formula, cells, allow_blank=True):
    dv = DataValidation(type="list", formula1="=" + rng_formula, allow_blank=allow_blank)
    dv.error = "Choose a value from the list."
    dv.errorTitle = "Invalid entry"
    ws.add_data_validation(dv)
    for part in cells.split():
        dv.add(part)


# ================================================================ README
R = sheet("ReadMe", "1F4E3D")
wb.move_sheet("ReadMe", offset=-1)
title(R, "GBF Headline Indicator 3.1 – National Calculation & Reporting Tool",
      "Coverage of protected areas and other effective area-based conservation measures (OECMs) – "
      "built on the official metadata (gbf-indicators.org/metadata/headline/3-1, updated 1 Sept 2024)")
readme = [
    ("PURPOSE", None),
    ("What this tool does", "Computes Headline Indicator 3.1 for Target 3 of the Kunming-Montreal Global Biodiversity Framework (KMGBF) at national level, "
     "plus the five disaggregations listed in the metadata: (1) PAs vs OECMs, (2) realm/biome/ecosystem, (3) Key Biodiversity Areas, "
     "(4) management effectiveness, (5) governance type. It also produces a time series, quality-control checks and a reporting dashboard."),
    ("What this tool does NOT do", "Excel cannot perform spatial operations. The metadata's steps 1–6 (filter, buffer points, merge, flatten/dissolve, erase PA from OECMs, "
     "intersect with base map, project to Mollweide) must be done in a GIS (QGIS, ArcGIS, R 'wdpar' package, Python geopandas). The tool takes the "
     "resulting areas and performs step 7 (coverage calculation), the disaggregations, the time series and the quality checks. "
     "If no GIS capacity exists, the tool falls back to reported/GIS areas per site and flags the result as an upper bound (overlaps may be double-counted)."),
    ("Relationship with Protected Planet", "UNEP-WCMC/IUCN publish monthly national statistics on Protected Planet computed with the same method. This tool lets a "
     "country (a) reproduce and reconcile those figures, (b) include national data not yet submitted to the WDPA/WD-OECM, (c) compute the "
     "disaggregations that are published only biennially or not at all for its own national ecosystem maps, and (d) document every step for the national report."),
    ("SHEET GUIDE", None),
    ("1. Setup", "Country, reporting year, realm areas (base-map denominators), method-compliance declarations, thresholds and optional GIS totals."),
    ("2. PA_OECM_Register", "One row per protected area / OECM using WDPA/WD-OECM attribute names. Applies the metadata inclusion filters automatically and flags data-quality issues."),
    ("3. Headline_3.1", "Headline indicator: % terrestrial & inland water and % marine & coastal area covered, split PA vs OECM, distance to the 30% target, inland waters."),
    ("4. Ecosystems", "Disaggregation by IUCN Global Ecosystem Typology biome, by Ecosystem Functional Group/ecoregion/national ecosystem type, and inland waters (rivers, lakes & wetlands)."),
    ("5. KBA_Coverage", "Mean % of each KBA covered by PAs and/or OECMs (aligned with SDG 14.5.1, 15.1.2, 15.4.1)."),
    ("6. Governance", "Coverage by WDPA governance type and the four IUCN governance types (proxy for 'equitably governed'); supplementary IUCN management categories."),
    ("7. Mgmt_Effectiveness", "Coverage by management-effectiveness class (PROVISIONAL – the official methodology is still under development)."),
    ("8. Time_Series", "Cumulative coverage by year from STATUS_YR, with the metadata's treatment of missing designation years."),
    ("9. QC_Checks", "Automated method-compliance and data-quality checks. Resolve every WARN before reporting."),
    ("10. Dashboard", "Summary figures and charts for the national report."),
    ("11. Metadata / References", "Summary of the official metadata (definitions, method, limitations) and the scientific references."),
    ("WORKFLOW", None),
    ("Step 1 – Data", "Download the national WDPA and WD-OECM (protectedplanet.net) and add any nationally recognised sites not yet reported. "
     "Download KBA polygons (keybiodiversityareas.org) and national ecosystem maps (cross-walked to the Global Ecosystem Typology)."),
    ("Step 2 – Filter", "Remove sites with STATUS 'Proposed' or 'Not Reported', points without REP_AREA, and UNESCO-MAB Biosphere Reserves (the register does this automatically; do the same in GIS)."),
    ("Step 3 – Buffer points", "Buffer point sites with a circle of area = REP_AREA (radius = √(REP_AREA/π), computed in the register column 'Buffer radius')."),
    ("Step 4 – Flatten & erase", "Merge polygons + buffered points; dissolve PAs into one flat layer. For OECMs: erase all areas overlapping PAs, then dissolve. "
     "To keep the time series exact, attribute each overlapping area to the EARLIEST-designated site (PAs before OECMs). "
     "Then TRANSFER site-level attributes (PAME, governance) from overlapping records that describe the same physical site to the record holding the area – "
     "otherwise the effectiveness and governance disaggregations are understated."),
    ("Step 5 – Intersect & project", "Intersect with the national base map (land + territorial sea/EEZ), project to Mollweide equal-area (ESRI:54009), compute km² for land and sea parts."),
    ("Step 6 – Enter", "Enter per-site net areas in the register (columns R–S) or the national flattened totals in Setup (override). Enter KBA and ecosystem overlap areas."),
    ("Step 7 – Check & report", "Review QC_Checks, then report from Headline_3.1 and Dashboard. Record dataset versions in Setup."),
    ("COLOUR LEGEND", None),
    ("Yellow cell, blue text", "INPUT – enter or paste data here."),
    ("Grey cell, black text", "CALCULATION – do not overwrite (formulas)."),
    ("Blue cell, bold", "KEY RESULT."),
    ("Orange rows", "EXAMPLE data from a FICTIONAL country, showing the expected format. Delete/overwrite before use."),
    ("Units", "All areas in km² (Mollweide equal-area). River length in km. Percentages stored as fractions (0.30 = 30%)."),
]
r = 4
for k, v in readme:
    if v is None:
        section(R, r, k, 2)
    else:
        put(R, f"A{r}", k, "label", bold=True)
        put(R, f"B{r}", v, "label")
        R.row_dimensions[r].height = max(15, 14 * (len(v) // 120 + 1))
    r += 1
for ref, fill in (("A{}".format(r - 5), fill_in), ("A{}".format(r - 4), fill_calc),
                  ("A{}".format(r - 3), fill_key), ("A{}".format(r - 2), fill_ex)):
    R[ref].fill = fill
widths(R, {"A": 30, "B": 140})

# ================================================================ SETUP
S = sheet("Setup", "C00000")
title(S, "1. Setup – country parameters, denominators and method declarations",
      "Fill every yellow cell. Areas must come from the SAME base map and projection used for the PA/OECM areas.")
header(S, 3, 1, ["Parameter", "Value", "Unit", "Notes / source (metadata 3.1)"], 30)
setup_rows = [
    # (row, label, value, unit, note, fmt, validation)
    (4, "Country / jurisdiction", "Example Country (fictional – replace)", "text", "", None, None),
    (5, "ISO3 code", "EXC", "text", "ISO 3166-1 alpha-3", None, None),
    (6, "Reporting year", 2026, "year", "Year of the national report / data cut-off", "0", None),
    (7, "WDPA / WD-OECM release used", "WDPA_WDOECM_Oct2026 (example)", "text", "Monthly release from protectedplanet.net; record month & year", None, None),
    (8, "KBA dataset version", "WDKBA 2026_01 (example)", "text", "World Database of KBAs (BirdLife International on behalf of the KBA Partnership)", None, None),
    (9, "Base map used", "National land boundary + EEZ (example)", "text", "Metadata: EEZ (VLIZ), World Vector Shoreline 3rd ed., GADM. National official boundaries are acceptable if documented", None, None),
    (10, "Terrestrial area (land incl. inland waters)", 160000, "km²", "Denominator, terrestrial realm. Mollweide equal-area. (Antarctica excluded globally)", KM2, None),
    (11, "Marine & coastal area (territorial sea + EEZ)", 100000, "km²", "Denominator, marine realm. Areas beyond national jurisdiction are excluded at national level", KM2, None),
    (12, "Target coverage", 0.30, "fraction", "KMGBF Target 3: at least 30% of terrestrial & inland water and of marine & coastal areas", PCT, None),
    (13, "Target year", 2030, "year", "", "0", None),
    (14, "PA layer flattened (overlaps dissolved) in GIS?", "Y", "Y/N", "Method step 4: flatten to avoid double counting", None, "yn"),
    (15, "OECM layer: PA overlap erased and flattened?", "Y", "Y/N", "OECM method step 4: erase areas where OECMs overlap PAs", None, "yn"),
    (16, "Areas computed in Mollweide equal-area projection?", "Y", "Y/N", "Method step 6", None, "yn"),
    (17, "Overlaps attributed to earliest-designated site?", "Y", "Y/N", "Needed for an exact time series from per-site net areas (tool recommendation, not in metadata)", None, "yn"),
    (18, "OPTIONAL GIS total – PA terrestrial (flattened)", None, "km²", "If entered, overrides the register sum in the headline (reconciliation shown in QC)", KM2, None),
    (19, "OPTIONAL GIS total – OECM terrestrial (PA-erased, flattened)", None, "km²", "As above", KM2, None),
    (20, "OPTIONAL GIS total – PA marine (flattened)", None, "km²", "As above", KM2, None),
    (21, "OPTIONAL GIS total – OECM marine (PA-erased, flattened)", None, "km²", "As above", KM2, None),
    (22, "KBA marine classification threshold", 0.05, "fraction", "Metadata: a KBA with ≥5% overlap with the ocean is classified as marine", PCT, None),
    (23, "KBA 'complete coverage' threshold", 0.98, "fraction", "Tolerance for digitisation error; 98% used by Butchart et al. (2012). National choice – document it", PCT, None),
    (24, "PAME 'High' class – minimum normalised score", 67, "score 0–100", "PROVISIONAL national choice; official effectiveness methodology still under development (UNEP-WCMC, IUCN & JNCC 2023)", "0", None),
    (25, "PAME 'Moderate' class – minimum normalised score", 33, "score 0–100", "PROVISIONAL national choice; scores below are 'Low'", "0", None),
    (26, "PAME validity window", 5, "years", "Assessments older than this are classed 'Assessment outdated'. National choice", "0", None),
    (27, "Time-series start year", 1900, "year", "Global series starts 1819; choose the year of the first national site or earlier", "0", None),
]
yn_cells = []
if CFG:
    setup_rows = [(r_, l_, CFG["setup"].get(str(r_), v_), u_, n_, f_, vv_) for r_, l_, v_, u_, n_, f_, vv_ in setup_rows]
for row, lab, val, unit, nt, fmt, v in setup_rows:
    put(S, f"A{row}", lab, "label", bold=True)
    put(S, f"B{row}", val, "in", fmt)
    put(S, f"C{row}", unit, "label")
    put(S, f"D{row}", nt, "label")
    if v == "yn":
        yn_cells.append(f"B{row}")
    if 4 <= row <= 11 and val is not None and row in (4, 5, 7, 8, 9):
        S[f"B{row}"].fill = fill_ex
dv_list(S, LR["Y/N"], " ".join(yn_cells))
widths(S, {"A": 52, "B": 38, "C": 12, "D": 110})
if CFG:
    for ref in ("B4", "B5", "B7", "B8", "B9"):
        S[ref].fill = fill_in
    note(S, "A29", CFG.get("setup_note", ""))
else:
    note(S, "A29", "Orange cells contain fictional example values – replace them. Realm areas (B10–B11) are also example values.")
    S["B10"].fill = fill_ex
    S["B11"].fill = fill_ex

SET = {k: f"Setup!$B${k}" for k in range(4, 28)}
YEAR, TERR, MAR, TGT = SET[6], SET[10], SET[11], SET[12]

# ================================================================ REGISTER
G = sheet("PA_OECM_Register", "2E75B6")
title(G, "2. PA & OECM register – one row per site (WDPA / WD-OECM attribute names)",
      "Columns A–Y = inputs. Columns Z–AL = automatic calculations. Net areas (R–S) come from the flattened GIS layers "
      "(metadata steps 1–6); if left blank, gross areas are used and flagged.")
N0, NROWS = 5, 1500
NN = N0 + NROWS - 1
cols = [
    # (letter, header, width, kind)
    ("A", "WDPAID / national ID", 14, "in"),
    ("B", "NAME", 30, "in"),
    ("C", "DESIG_ENG (designation)", 24, "in"),
    ("D", "DESIG_TYPE", 13, "in"),
    ("E", "Site type (PA / OECM)\n[WDPA PA_DEF 1/0]", 12, "in"),
    ("F", "IUCN_CAT", 11, "in"),
    ("G", "GOV_TYPE", 30, "in"),
    ("H", "STATUS", 13, "in"),
    ("I", "STATUS_YR\n(0/blank = unknown)", 11, "in"),
    ("J", "MARINE\n0=terr., 1=coastal, 2=marine", 12, "in"),
    ("K", "Geometry\n(Polygon / Point)", 11, "in"),
    ("L", "REP_AREA\n(km²)", 11, "in"),
    ("M", "REP_M_AREA\n(km²)", 11, "in"),
    ("N", "GIS_AREA\n(km², Mollweide)", 11, "in"),
    ("O", "GIS_M_AREA\n(km², Mollweide)", 11, "in"),
    ("P", "UNESCO-MAB Biosphere Reserve? (Y/N)", 12, "in"),
    ("Q", "MAB exception: count anyway? (Y/N)", 12, "in"),
    ("R", "NET terrestrial area after flattening / PA-erase (km²)", 15, "in"),
    ("S", "NET marine area after flattening / PA-erase (km²)", 15, "in"),
    ("T", "PAME assessed? (Y/N)", 10, "in"),
    ("U", "PAME tool", 18, "in"),
    ("V", "PAME year", 9, "in"),
    ("W", "PAME score (normalised 0–100)", 11, "in"),
    ("X", "Effectiveness class – manual override (optional)", 15, "in"),
    ("Y", "Notes / source", 22, "in"),
    ("Z", "INCLUDED in indicator (1/0)", 10, "calc"),
    ("AA", "Exclusion reason", 26, "calc"),
    ("AB", "Gross total area used (km²)", 12, "calc"),
    ("AC", "Gross marine area (km²)", 12, "calc"),
    ("AD", "Gross terrestrial area (km²)", 12, "calc"),
    ("AE", "Net area supplied? (1/0)", 9, "calc"),
    ("AF", "TERRESTRIAL area counted (km²)", 13, "calc"),
    ("AG", "MARINE area counted (km²)", 13, "calc"),
    ("AH", "Designation year known (0 = missing)", 11, "calc"),
    ("AI", "Point buffer radius (km) = √(REP_AREA/π)", 12, "calc"),
    ("AJ", "IUCN governance type (A–D)", 30, "calc"),
    ("AK", "Effectiveness class", 18, "calc"),
    ("AL", "QC flags", 60, "calc"),
]
for i, (c, h, w, k) in enumerate(cols):
    cell = G[f"{c}4"]
    cell.value = h
    cell.font = f_hdr
    cell.fill = fill_hdr if k == "in" else PatternFill("solid", fgColor="595959")
    cell.alignment = center
    cell.border = bord
    G.column_dimensions[c].width = w
G.row_dimensions[4].height = 80
G["A3"] = "INPUTS (A–Y)"
G["A3"].font = f_sub
G["Z3"] = "CALCULATIONS (Z–AL) – do not edit"
G["Z3"].font = f_sub
G.freeze_panes = "C5"

for r in range(N0, NN + 1):
    blank = f'AND($A{r}="",$B{r}="")'
    f = {
        "Z": f'=IF({blank},"",IF(OR($E{r}="",$H{r}="",$H{r}="Proposed",$H{r}="Not Reported"),0,'
             f'IF(AND($P{r}="Y",$Q{r}<>"Y"),0,IF(AND($K{r}="Point",N($L{r})<=0),0,'
             f'IF(AND(N($L{r})<=0,N($N{r})<=0,N($R{r})+N($S{r})<=0),0,1)))))',
        "AA": f'=IF({blank},"",IF($E{r}="","Site type missing",IF($H{r}="","STATUS missing",'
              f'IF($H{r}="Proposed","STATUS = Proposed",IF($H{r}="Not Reported","STATUS = Not Reported",'
              f'IF(AND($P{r}="Y",$Q{r}<>"Y"),"UNESCO-MAB Biosphere Reserve",'
              f'IF(AND($K{r}="Point",N($L{r})<=0),"Point without REP_AREA",'
              f'IF(AND(N($L{r})<=0,N($N{r})<=0,N($R{r})+N($S{r})<=0),"No area information",""))))))))',
        "AB": f'=IF({blank},"",IF($K{r}="Point",N($L{r}),IF(N($N{r})>0,N($N{r}),N($L{r}))))',
        "AC": f'=IF({blank},"",MIN(AB{r},IF(N($J{r})=0,0,IF(N($J{r})=2,AB{r},'
              f'IF(AND($K{r}<>"Point",N($O{r})>0),N($O{r}),N($M{r}))))))',
        "AD": f'=IF({blank},"",MAX(0,AB{r}-AC{r}))',
        "AE": f'=IF({blank},"",IF(OR($R{r}<>"",$S{r}<>""),1,0))',
        "AF": f'=IF({blank},"",IF(Z{r}=1,IF(AE{r}=1,N($R{r}),AD{r}),0))',
        "AG": f'=IF({blank},"",IF(Z{r}=1,IF(AE{r}=1,N($S{r}),AC{r}),0))',
        "AH": f'=IF({blank},"",IF(AND(ISNUMBER($I{r}),N($I{r})>0),$I{r},0))',
        "AI": f'=IF(AND(NOT({blank}),$K{r}="Point",N($L{r})>0),SQRT(N($L{r})/PI()),"")',
        "AJ": f'=IF({blank},"",IFERROR(VLOOKUP($G{r},{GOV_TABLE},2,FALSE),"Not reported"))',
        "AK": f'=IF({blank},"",IF($X{r}<>"",$X{r},IF($T{r}<>"Y","Not assessed",'
              f'IF(AND(ISNUMBER($V{r}),{YEAR}-$V{r}>{SET[26]}),"Assessment outdated",'
              f'IF(NOT(ISNUMBER($W{r})),"Assessed – no score",'
              f'IF($W{r}>={SET[24]},"High",IF($W{r}>={SET[25]},"Moderate","Low")))))))',
        "AL": f'=IF({blank},"",IF(Z{r}=0,"",'
              f'IF(AND(AE{r}=1,N($R{r})>AD{r}*1.01+0.001),"Net terrestrial > gross; ","")&'
              f'IF(AND(AE{r}=1,N($S{r})>AC{r}*1.01+0.001),"Net marine > gross; ","")&'
              f'IF(AE{r}=0,"No net area – gross used, overlaps may be double-counted; ","")&'
              f'IF(AH{r}=0,"STATUS_YR missing – imputed in time series; ","")&'
              f'IF(AND(ISNUMBER($I{r}),N($I{r})>{YEAR}),"STATUS_YR after reporting year; ","")&'
              f'IF(OR($G{r}="",$G{r}="Not Reported"),"GOV_TYPE not reported; ","")&'
              f'IF(AND(N($J{r})=1,$K{r}="Point",N($M{r})<=0),"Coastal point without REP_M_AREA – land/sea split unknown; ","")&'
              f'IF(AND(N($J{r})=0,N($S{r})>0),"MARINE=0 but net marine >0; ","")&'
              f'IF(AND(N($J{r})=2,N($R{r})>0),"MARINE=2 but net terrestrial >0; ","")&'
              f'IF($K{r}="Point","Buffered point – coverage approximate; ","")))',
    }
    for c, formula in f.items():
        cell = G[f"{c}{r}"]
        cell.value = formula
        cell.font, cell.fill = f_base, fill_calc
    for c in ("AB", "AC", "AD", "AF", "AG"):
        G[f"{c}{r}"].number_format = KM2
    G[f"AI{r}"].number_format = "0.00"
    for c in "ABCDEFGHIJKLMNOPQRSTUVWXY":
        cell = G[f"{c}{r}"]
        cell.font, cell.fill = f_in, fill_in
    for c in "LMNORS":
        G[f"{c}{r}"].number_format = KM2

rng = lambda c: f"{c}{N0}:{c}{NN}"
dv_list(G, LR["Site type"], rng("E"))
dv_list(G, LR["IUCN_CAT"], rng("F"))
dv_list(G, GOV_RANGE, rng("G"))
dv_list(G, LR["STATUS"], rng("H"))
dv_list(G, LR["MARINE"], rng("J"))
dv_list(G, LR["Geometry"], rng("K"))
dv_list(G, LR["Y/N"], f"{rng('P')} {rng('Q')} {rng('T')}")
dv_list(G, LR["DESIG_TYPE"], rng("D"))
dv_list(G, LR["PAME tool"], rng("U"))
dv_list(G, LR["PAME class"], rng("X"))
for c in "ILMNORSW":
    dv = DataValidation(type="decimal", operator="greaterThanOrEqual", formula1="0", allow_blank=True)
    dv.error = "Enter a non-negative number."
    G.add_data_validation(dv)
    dv.add(rng(c))

examples = [
    # A..Y
    ["EX-0001", "EXAMPLE – Mountain National Park", "National Park", "National", "PA", "II", "Federal or national ministry or agency",
     "Designated", 1975, 0, "Polygon", 4200, 0, 4185.3, 0, "N", "", 4185.3, 0, "Y", "METT", 2023, 72, "", "Example row"],
    ["EX-0002", "EXAMPLE – Blue Bay Marine Park", "Marine Park", "National", "PA", "II", "Federal or national ministry or agency",
     "Designated", 2005, 2, "Polygon", 12000, 12000, 11950.0, 11950.0, "N", "", 0, 11950.0, "Y", "IMET", 2019, 55, "", "Example row"],
    ["EX-0003", "EXAMPLE – Delta Wetland Reserve (Ramsar overlap)", "Nature Reserve", "National", "PA", "IV", "Collaborative governance",
     "Designated", 1990, 1, "Polygon", 2600, 1500, 2500.0, 1500.0, "N", "", 980.0, 1500.0, "N", "", "", "", "", "Overlap with EX-0001 removed in GIS"],
    ["EX-0004", "EXAMPLE – Community Forest Reserve", "Community Reserve", "National", "PA", "VI", "Local communities",
     "Established", "", 0, "Point", 350, 0, "", "", "N", "", 350.0, 0, "N", "", "", "", "", "STATUS_YR unknown"],
    ["EX-0005", "EXAMPLE – Northern Hills (proposed)", "National Park", "National", "PA", "Not Reported", "Federal or national ministry or agency",
     "Proposed", "", 0, "Polygon", 1800, 0, 1795.0, 0, "N", "", "", "", "N", "", "", "", "", "Excluded: proposed"],
    ["EX-0006", "EXAMPLE – Coastal Biosphere Reserve", "UNESCO-MAB Biosphere Reserve", "International", "PA", "Not Applicable",
     "Federal or national ministry or agency", "Designated", 2001, 1, "Polygon", 9000, 4000, 8950.0, 3980.0, "Y", "N", "", "", "N", "", "", "", "", "Excluded: MAB"],
    ["EX-0007", "EXAMPLE – Ancestral Territory Conserved Area", "Indigenous conserved area (OECM)", "National", "OECM", "Not Applicable",
     "Indigenous peoples", "Established", 2021, 0, "Polygon", 6000, 0, 5980.0, 0, "N", "", 5200.0, 0, "Y", "SAGE (governance & equity)", 2024, "", "", "PA overlap erased"],
    ["EX-0008", "EXAMPLE – Reef Fisheries Closure", "Fisheries closure (OECM)", "National", "OECM", "Not Applicable",
     "Federal or national ministry or agency", "Established", 2019, 2, "Polygon", 8000, 8000, 7990.0, 7990.0, "N", "", 0, 7600.0, "N", "", "", "", "", "PA overlap erased"],
]
if CFG:
    examples = CFG["register"]
for i, row in enumerate(examples):
    r = N0 + i
    for j, v in enumerate(row):
        c = G.cell(row=r, column=j + 1, value=None if v == "" else v)
        if not CFG:
            c.fill = fill_ex
if not CFG: G[f"A{N0}"].comment = Comment("Orange rows are FICTIONAL examples showing the expected format. Overwrite or delete them.", "Tool")

# Register ranges for other sheets
REG = "PA_OECM_Register!"
RG = {c: f"{REG}${c}${N0}:${c}${NN}" for c in
      ["E", "F", "G", "I", "Z", "AE", "AF", "AG", "AH", "AJ", "AK", "AL", "K", "AA"]}
INC, TYP, TER, MRN, YR = RG["Z"], RG["E"], RG["AF"], RG["AG"], RG["AH"]

# ================================================================ HEADLINE
H = sheet("Headline_3.1", "00B050")
title(H, "3. Headline indicator 3.1 – coverage of protected areas and OECMs",
      "Coverage = (PA area + OECM area, overlaps removed) ÷ realm area. OECM area is computed after erasing overlaps with PAs, so PA + OECM never double-counts.")
section(H, 4, "A. Coverage by realm (disaggregation 1: PA vs OECM; disaggregation 2: realm)", 14)
header(H, 5, 1, ["Realm", "Realm area (km²)", "PA area – register sum (km²)", "OECM area – register sum (km²)",
                 "PA area USED (km²)", "OECM area USED (km²)", "PA + OECM area (km²)", "PA coverage (%)", "OECM coverage (%)",
                 "INDICATOR 3.1 – total coverage (%)", "Target (%)", "Gap to target (percentage points)",
                 "Additional area needed (km²)", "Status"], 60)
for row, realm, area, colname, ov_pa, ov_oe in ((6, "Terrestrial & inland waters", TERR, "AF", SET[18], SET[19]),
                                                (7, "Marine & coastal", MAR, "AG", SET[20], SET[21])):
    put(H, f"A{row}", realm, "label", bold=True)
    put(H, f"B{row}", f"={area}", "link", KM2)
    put(H, f"C{row}", f'=SUMIFS({REG}${colname}${N0}:${colname}${NN},{INC},1,{TYP},"PA")', fmt=KM2)
    put(H, f"D{row}", f'=SUMIFS({REG}${colname}${N0}:${colname}${NN},{INC},1,{TYP},"OECM")', fmt=KM2)
    put(H, f"E{row}", f'=IF(ISNUMBER({ov_pa}),{ov_pa},C{row})', fmt=KM2)
    put(H, f"F{row}", f'=IF(ISNUMBER({ov_oe}),{ov_oe},D{row})', fmt=KM2)
    put(H, f"G{row}", f"=E{row}+F{row}", fmt=KM2)
    put(H, f"H{row}", f'=IF(N(B{row})>0,E{row}/B{row},"")', fmt=PCT)
    put(H, f"I{row}", f'=IF(N(B{row})>0,F{row}/B{row},"")', fmt=PCT)
    put(H, f"J{row}", f'=IF(N(B{row})>0,G{row}/B{row},"")', "key", PCT)
    put(H, f"K{row}", f"={TGT}", "link", PCT)
    put(H, f"L{row}", f'=IF(J{row}="","",MAX(0,K{row}-J{row})*100)', fmt="0.0")
    put(H, f"M{row}", f'=IF(J{row}="","",MAX(0,K{row}*B{row}-G{row}))', fmt=KM2)
    put(H, f"N{row}", f'=IF(J{row}="",IF(N(B{row})=0,"Not applicable (no area in this realm)","Enter realm area in Setup"),IF(J{row}>=K{row},"Target met","Below target"))')
note(H, "A8", "‘USED’ = Setup GIS override if entered, otherwise register sum. Gap in percentage points. "
              "Coverage >100% indicates an error in areas or denominators (see QC_Checks).")

section(H, 10, "B. Share of the conserved estate (relative contribution of PAs and OECMs)", 14)
header(H, 11, 1, ["Realm", "PA share of PA+OECM area (%)", "OECM share of PA+OECM area (%)"], 45)
for row, src in ((12, 6), (13, 7)):
    put(H, f"A{row}", f"=A{src}", "label", bold=True)
    put(H, f"B{row}", f'=IF(G{src}>0,E{src}/G{src},"")', fmt=PCT)
    put(H, f"C{row}", f'=IF(G{src}>0,F{src}/G{src},"")', fmt=PCT)

section(H, 15, "C. Inland waters (metadata: separate methodology – river length via RiverATLAS; lakes & wetlands via GLWD v2) – inputs on 'Ecosystems' sheet", 14)
header(H, 16, 1, ["Inland water component", "Total extent", "Unit", "Covered by PAs", "Covered by OECMs", "PA + OECM",
                  "Coverage (%)", "Target (%)", "Status"], 45)
for row, src, lab in ((17, 52, "Rivers and streams (length)"), (18, 53, "Lakes and wetlands (area)")):
    put(H, f"A{row}", lab, "label", bold=True)
    put(H, f"B{row}", f"=Ecosystems!B{src}", "link", KM2)
    put(H, f"C{row}", f"=Ecosystems!C{src}", "link")
    put(H, f"D{row}", f"=Ecosystems!D{src}", "link", KM2)
    put(H, f"E{row}", f"=Ecosystems!E{src}", "link", KM2)
    put(H, f"F{row}", f"=D{row}+E{row}", fmt=KM2)
    put(H, f"G{row}", f'=IF(N(B{row})>0,F{row}/B{row},"")', "key", PCT)
    put(H, f"H{row}", f"={TGT}", "link", PCT)
    put(H, f"I{row}", f'=IF(G{row}="","No data",IF(G{row}>=H{row},"Target met","Below target"))')

section(H, 20, "D. Site counts and data basis", 14)
header(H, 21, 1, ["Item", "PAs", "OECMs", "Total"], 30)
items = [
    ("Sites in register", f'COUNTIFS({TYP},"{{t}}")'),
    ("Sites INCLUDED in indicator", f'COUNTIFS({INC},1,{TYP},"{{t}}")'),
    ("Sites EXCLUDED (proposed, not reported, MAB, no area)", f'COUNTIFS({INC},0,{TYP},"{{t}}")'),
    ("Included point sites (buffered)", f'COUNTIFS({INC},1,{TYP},"{{t}}",{RG["K"]},"Point")'),
    ("Included sites without net (flattened) area – gross used", f'COUNTIFS({INC},1,{TYP},"{{t}}",{RG["AE"]},0)'),
    ("Included sites with unknown STATUS_YR", f'COUNTIFS({INC},1,{TYP},"{{t}}",{YR},0)'),
]
for i, (lab, tmpl) in enumerate(items):
    row = 22 + i
    put(H, f"A{row}", lab, "label")
    put(H, f"B{row}", "=" + tmpl.replace("{t}", "PA"), fmt="#,##0")
    put(H, f"C{row}", "=" + tmpl.replace("{t}", "OECM"), fmt="#,##0")
    put(H, f"D{row}", f"=B{row}+C{row}", fmt="#,##0")
row = 29
put(H, f"A{row}", "Share of counted area based on flattened (net) GIS values", "label", bold=True)
put(H, f"B{row}", f'=IFERROR((SUMIFS({TER},{INC},1,{RG["AE"]},1)+SUMIFS({MRN},{INC},1,{RG["AE"]},1))/(SUM({TER})+SUM({MRN})),"")',
    "key", PCT)
put(H, f"C{row}", "Should be 100% for an official figure; below 100% the result is an upper bound.", "label")
widths(H, {"A": 46, "B": 16, "C": 16, "D": 16, "E": 16, "F": 16, "G": 16, "H": 14, "I": 14, "J": 18,
           "K": 10, "L": 14, "M": 16, "N": 22})
H.conditional_formatting.add("N6:N7", CellIsRule(operator="equal", formula=['"Target met"'],
                                                 fill=PatternFill("solid", fgColor="C6EFCE")))
H.conditional_formatting.add("N6:N7", CellIsRule(operator="equal", formula=['"Below target"'],
                                                 fill=PatternFill("solid", fgColor="FFC7CE")))

# ================================================================ ECOSYSTEMS
E = sheet("Ecosystems", "7030A0")
title(E, "4. Disaggregation by ecosystem – IUCN Global Ecosystem Typology (Keith et al. 2022) and ecoregions",
      "Metadata national approach: (1) match national ecosystem maps to GET; (2) overlay PA/OECM flat layers; (3) exclude inappropriate groups; "
      "(4) aggregate EFGs to biomes; (5) inland waters as river length and lake/wetland area.")
section(E, 4, "A. Coverage by GET biome (25 biomes). Enter extent and PA/OECM overlap from GIS (same flattened layers as the headline).", 12)
header(E, 5, 1, ["GET code", "Realm", "Biome", "Include in assessment? (Y/N)", "Unit", "Total extent", "Covered by PAs",
                 "Covered by OECMs (PA-erased)", "PA + OECM", "Coverage (%)", "≥ target?", "QC"], 45)
B0 = 6
ex_biome = {"T1": (52000, 9100, 2600), "T4": (61000, 6200, 2100), "T5": (18000, 400, 300), "TF1": (2400, 650, 150),
            "M1": (38000, 9800, 3100), "M2": (55000, 2800, 4200), "MT1": (900, 310, 40)}
if CFG:
    ex_biome = {k: tuple(v) for k, v in CFG.get("biomes", {}).items()}
for i, (code, realm, name, inc, unit) in enumerate(biomes):
    r = B0 + i
    put(E, f"A{r}", code, "label", bold=True)
    put(E, f"B{r}", realm, "label")
    put(E, f"C{r}", name, "label")
    put(E, f"D{r}", inc, "in")
    put(E, f"E{r}", unit, "label")
    vals = ex_biome.get(code, (None, None, None))
    for col, v in zip("FGH", vals):
        c = put(E, f"{col}{r}", v, "in", KM2)
        if v is not None and not CFG:
            c.fill = fill_ex
    put(E, f"I{r}", f'=IF(F{r}="","",N(G{r})+N(H{r}))', fmt=KM2)
    put(E, f"J{r}", f'=IF(N(F{r})>0,I{r}/F{r},"")', fmt=PCT)
    put(E, f"K{r}", f'=IF(J{r}="","",IF(J{r}>={TGT},"Yes","No"))')
    put(E, f"L{r}", f'=IF(J{r}="","",IF(J{r}>1.001,"Covered > extent – check",""))')
BN = B0 + len(biomes) - 1
dv_list(E, LR["Y/N"], f"D{B0}:D{BN}")
note(E, f"A{BN + 1}", "Default 'N' for anthropogenic biomes (T7, S2, SF2, F3, M4, MT3) and subterranean biomes rarely mappable at national scale – "
                       "a national choice; the metadata recommends excluding groups that are inappropriate or affected by data-resolution errors.")

section(E, 33, "B. Biome summary (included biomes with data)", 12)
header(E, 34, 1, ["Metric", "Value"], 30)
pct_r, inc_r = f"$J${B0}:$J${BN}", f"$D${B0}:$D${BN}"
summ = [
    ("Biomes assessed (included, with extent)", f'=COUNTIFS({inc_r},"Y",{pct_r},">=0")', "0"),
    ("Biomes with coverage ≥ target", f'=COUNTIFS({inc_r},"Y",{pct_r},">="&{TGT})', "0"),
    ("Share of assessed biomes ≥ target", '=IF(B35>0,B36/B35,"")', PCT),
    ("Mean biome coverage (%)", f'=IFERROR(AVERAGEIFS({pct_r},{inc_r},"Y"),"")', PCT),
    ("Minimum biome coverage (%)", f'=IF(B35>0,_xlfn.MINIFS({pct_r},{inc_r},"Y"),"")', PCT),
    ("Maximum biome coverage (%)", f'=IF(B35>0,_xlfn.MAXIFS({pct_r},{inc_r},"Y"),"")', PCT),
]
for i, (lab, fm, fmt) in enumerate(summ):
    put(E, f"A{35 + i}", lab, "label", bold=True)
    put(E, f"B{35 + i}", fm, "key" if i in (2, 3) else "calc", fmt)

section(E, 50, "C. Inland waters – headline inland-water coverage (RiverATLAS, Linke et al. 2019; GLWD v2, Lehner et al. 2024 – or national hydrography)", 12)
header(E, 51, 1, ["Component", "Total extent", "Unit", "Covered by PAs", "Covered by OECMs (PA-erased)", "Coverage (%)"], 40)
iw = CFG.get("inland", [[None] * 3, [None] * 3]) if CFG else [(12000, 1800, 600), (900, 210, 90)]
for r, lab, unit, vals in ((52, "Rivers and streams", "km (length)", iw[0]),
                           (53, "Lakes and wetlands", "km²", iw[1])):
    put(E, f"A{r}", lab, "label", bold=True)
    put(E, f"C{r}", unit, "label")
    for col, val in zip("BDE", vals):
        c = put(E, f"{col}{r}", val, "in", KM2)
        if val is not None and not CFG:
            c.fill = fill_ex
    put(E, f"F{r}", f'=IF(N(B{r})>0,(N(D{r})+N(E{r}))/B{r},"")', "key", PCT)

section(E, 56, "D. Detailed units – Ecosystem Functional Groups, ecoregions or national ecosystem types (one row per unit)", 12)
header(E, 57, 1, ["Unit level", "Code", "Unit name", "Parent GET biome", "Include? (Y/N)", "Total extent (km² or km)",
                  "Covered by PAs", "Covered by OECMs (PA-erased)", "PA + OECM", "Coverage (%)", "≥ target?", "QC"], 45)
D0, DN = 58, 58 + 299
ex_units = [("GET Ecosystem Functional Group", "T1.1", "Tropical/Subtropical lowland rainforests", "T1", "Y", 30000, 6100, 1500),
            ("Terrestrial ecoregion (Dinerstein et al. 2017)", "ECO-000", "EXAMPLE ecoregion (fictional)", "T4", "Y", 41000, 3900, 1100),
            ("Marine ecoregion (Spalding et al. 2007)", "MEOW-000", "EXAMPLE marine ecoregion (fictional)", "M1", "Y", 60000, 11800, 6900)]
for r in range(D0, DN + 1):
    for col in "ABCDEFGH":
        put(E, f"{col}{r}", None, "in", KM2 if col in "FGH" else None)
    put(E, f"I{r}", f'=IF(F{r}="","",N(G{r})+N(H{r}))', fmt=KM2)
    put(E, f"J{r}", f'=IF(N(F{r})>0,I{r}/F{r},"")', fmt=PCT)
    put(E, f"K{r}", f'=IF(J{r}="","",IF(J{r}>={TGT},"Yes","No"))')
    put(E, f"L{r}", f'=IF(J{r}="","",IF(J{r}>1.001,"Covered > extent – check",""))')
if CFG:
    ex_units = CFG.get("units", [])
for i, row in enumerate(ex_units):
    for j, v in enumerate(row):
        c = E.cell(row=D0 + i, column=j + 1, value=v)
        if not CFG:
            c.fill = fill_ex
dv_list(E, LR["Ecosystem unit level"], f"A{D0}:A{DN}")
dv_list(E, BIOME_RANGE, f"D{D0}:D{DN}")
dv_list(E, LR["Y/N"], f"E{D0}:E{DN}")

section(E, 42, "E. Summary by detailed unit level (from table D)", 12)
header(E, 43, 1, ["Unit level", "Units assessed", "Units ≥ target", "Share ≥ target", "Mean coverage (%)", "Minimum coverage (%)"], 40)
lvl_r, dinc, dpct = f"$A${D0}:$A${DN}", f"$E${D0}:$E${DN}", f"$J${D0}:$J${DN}"
for i in range(6):
    r = 44 + i
    put(E, f"A{r}", f"=Lists!L{4 + i}", "label", bold=True)
    put(E, f"B{r}", f'=COUNTIFS({lvl_r},A{r},{dinc},"Y",{dpct},">=0")', fmt="0")
    put(E, f"C{r}", f'=COUNTIFS({lvl_r},A{r},{dinc},"Y",{dpct},">="&{TGT})', fmt="0")
    put(E, f"D{r}", f'=IF(B{r}>0,C{r}/B{r},"")', fmt=PCT)
    put(E, f"E{r}", f'=IFERROR(AVERAGEIFS({dpct},{lvl_r},A{r},{dinc},"Y"),"")', fmt=PCT)
    put(E, f"F{r}", f'=IF(B{r}>0,_xlfn.MINIFS({dpct},{lvl_r},A{r},{dinc},"Y"),"")', fmt=PCT)
widths(E, {"A": 44, "B": 22, "C": 40, "D": 14, "E": 14, "F": 16, "G": 14, "H": 16, "I": 14, "J": 13, "K": 10, "L": 24})
E.freeze_panes = "A6"
for rg in (f"J{B0}:J{BN}", f"J{D0}:J{DN}"):
    E.conditional_formatting.add(rg, FormulaRule(formula=[f'AND(ISNUMBER({rg.split(":")[0]}),{rg.split(":")[0]}>={TGT})'],
                                                 fill=PatternFill("solid", fgColor="C6EFCE")))

# ================================================================ KBA
K = sheet("KBA_Coverage", "FFC000")
title(K, "5. Coverage of Key Biodiversity Areas by PAs and/or OECMs",
      "Indicator = mean % of each KBA covered (Butchart et al. 2012, 2015). Overlaps: intersect each KBA with the flat PA layer and the PA-erased OECM layer.")
section(K, 4, "A. Summary (aligned with SDG 14.5.1 marine, 15.1.2 terrestrial & freshwater, 15.4.1 mountain)", 11)
header(K, 5, 1, ["KBA group", "Related SDG indicator", "Number of KBAs", "Mean % covered by PAs + OECMs",
                 "Mean % covered by PAs only", "Mean additional % from OECMs", "KBAs with no coverage",
                 "KBAs partially covered", "KBAs completely covered", "% of KBAs completely covered"], 55)
K0, KN = 16, 16 + 499
kr = lambda c: f"${c}${K0}:${c}${KN}"
groups = [("All KBAs", "—", None), ("Terrestrial KBAs", "SDG 15.1.2", "E"), ("Freshwater KBAs", "SDG 15.1.2", "F"),
          ("Marine KBAs (≥ threshold ocean overlap)", "SDG 14.5.1", "J"), ("Mountain KBAs", "SDG 15.4.1", "G")]
for i, (lab, sdg, flag) in enumerate(groups):
    r = 6 + i
    crit = f',{kr(flag)},"Y"' if flag else ""
    put(K, f"A{r}", lab, "label", bold=True)
    put(K, f"B{r}", sdg, "label")
    put(K, f"C{r}", f'=COUNTIFS({kr("L")},">=0"{crit})', fmt="0")
    put(K, f"D{r}", f'=IFERROR(AVERAGEIFS({kr("L")},{kr("L")},">=0"{crit}),"")', "key", PCT)
    put(K, f"E{r}", f'=IFERROR(AVERAGEIFS({kr("M")},{kr("L")},">=0"{crit}),"")', fmt=PCT)
    put(K, f"F{r}", f'=IF(D{r}="","",D{r}-E{r})', fmt=PCT)
    put(K, f"G{r}", f'=COUNTIFS({kr("O")},"None"{crit})', fmt="0")
    put(K, f"H{r}", f'=COUNTIFS({kr("O")},"Partial"{crit})', fmt="0")
    put(K, f"I{r}", f'=COUNTIFS({kr("O")},"Complete"{crit})', fmt="0")
    put(K, f"J{r}", f'=IF(C{r}>0,I{r}/C{r},"")', fmt=PCT)
note(K, "A12", "A KBA can belong to several groups (e.g. terrestrial and freshwater; marine and terrestrial) and is then counted in each, as in the metadata. "
               "'Complete' uses the threshold in Setup (B23).")

section(K, 14, "B. KBA list – one row per KBA (World Database of KBAs SitRecID)", 16)
header(K, 15, 1, ["SitRecID", "KBA name", "KBA area (km²)", "Fraction overlapping ocean (0–1)", "Terrestrial? (Y/N)",
                  "Freshwater? (Y/N)", "Mountain? (Y/N)", "Area covered by PAs (km², flattened)",
                  "Area covered by OECMs (km², PA-erased)", "Marine? (auto)", "PA + OECM covered (km²)",
                  "% covered (PA+OECM)", "% covered (PA only)", "% added by OECMs", "Coverage class", "QC"], 60)
ex_kba = [(90001, "EXAMPLE KBA – Mountain forest", 820, 0, "Y", "N", "Y", 790, 0),
          (90002, "EXAMPLE KBA – Delta wetlands", 1450, 0.32, "Y", "Y", "N", 610, 120),
          (90003, "EXAMPLE KBA – Outer reef", 300, 1, "N", "N", "N", 0, 0)]
for r in range(K0, KN + 1):
    for col in "ABCDEFGHI":
        put(K, f"{col}{r}", None, "in", KM2 if col in "CHI" else ("0.00" if col == "D" else None))
    put(K, f"J{r}", f'=IF(C{r}="","",IF(N(D{r})>={SET[22]},"Y","N"))')
    put(K, f"K{r}", f'=IF(C{r}="","",N(H{r})+N(I{r}))', fmt=KM2)
    put(K, f"L{r}", f'=IF(N(C{r})>0,MIN(1,K{r}/C{r}),"")', fmt=PCT)
    put(K, f"M{r}", f'=IF(N(C{r})>0,MIN(1,N(H{r})/C{r}),"")', fmt=PCT)
    put(K, f"N{r}", f'=IF(L{r}="","",L{r}-M{r})', fmt=PCT)
    put(K, f"O{r}", f'=IF(L{r}="","",IF(L{r}>={SET[23]},"Complete",IF(L{r}>0,"Partial","None")))')
    put(K, f"P{r}", f'=IF(C{r}="","",IF(K{r}>C{r}*1.01,"Covered area > KBA area – check overlap; ","")&'
                    f'IF(AND(E{r}<>"Y",F{r}<>"Y",J{r}<>"Y"),"No realm assigned; ",""))')
if CFG:
    ex_kba = CFG.get("kba", [])
for i, row in enumerate(ex_kba):
    for j, v in enumerate(row):
        c = K.cell(row=K0 + i, column=j + 1, value=v)
        if not CFG:
            c.fill = fill_ex
dv_list(K, LR["Y/N"], f"E{K0}:G{KN}")
widths(K, {"A": 36, "B": 34, "C": 13, "D": 13, "E": 11, "F": 11, "G": 11, "H": 15, "I": 15, "J": 10,
           "K": 14, "L": 13, "M": 13, "N": 13, "O": 13, "P": 36})
K.freeze_panes = f"C{K0}"

# ================================================================ GOVERNANCE
GV = sheet("Governance", "ED7D31")
title(GV, "6. Coverage by governance type (proxy for 'equitably governed' – Target 3)",
      "Governance types as reported in WDPA GOV_TYPE, grouped into the four IUCN governance types (Borrini-Feyerabend et al. 2013). "
      "IPLC territories are NOT added as a third category; only PAs/OECMs governed by IPs/LCs are counted (metadata).")
gcols = ["Governance", "Sites (included)", "Terrestrial – PA (km²)", "Terrestrial – OECM (km²)", "Terrestrial – total (km²)",
         "% of terrestrial realm", "% of terrestrial PA+OECM area", "Marine – PA (km²)", "Marine – OECM (km²)",
         "Marine – total (km²)", "% of marine realm", "% of marine PA+OECM area"]


def disagg_table(ws, start, labels, keyrange, extra_blank=False):
    header(ws, start, 1, gcols, 50)
    first = start + 1
    for i, lab in enumerate(labels):
        r = first + i
        put(ws, f"A{r}", lab, "label", bold=True)

        def s(area, typ):
            base = f'SUMIFS({area},{INC},1,{TYP},"{typ}",{keyrange},$A{r})'
            if extra_blank and lab == "Not Reported":
                base += f'+SUMIFS({area},{INC},1,{TYP},"{typ}",{keyrange},"")'
            return "=" + base
        cnt = f'=COUNTIFS({INC},1,{keyrange},$A{r})' + (f'+COUNTIFS({INC},1,{keyrange},"")' if extra_blank and lab == "Not Reported" else "")
        put(ws, f"B{r}", cnt, fmt="0")
        put(ws, f"C{r}", s(TER, "PA"), fmt=KM2)
        put(ws, f"D{r}", s(TER, "OECM"), fmt=KM2)
        put(ws, f"E{r}", f"=C{r}+D{r}", fmt=KM2)
        put(ws, f"F{r}", f'=IF(N({TERR})>0,E{r}/{TERR},"")', fmt=PCT)
        put(ws, f"H{r}", s(MRN, "PA"), fmt=KM2)
        put(ws, f"I{r}", s(MRN, "OECM"), fmt=KM2)
        put(ws, f"J{r}", f"=H{r}+I{r}", fmt=KM2)
        put(ws, f"K{r}", f'=IF(N({MAR})>0,J{r}/{MAR},"")', fmt=PCT)
    last = first + len(labels) - 1
    tr = last + 1
    put(ws, f"A{tr}", "TOTAL", "label", bold=True)
    for col in "BCDEHIJ":
        put(ws, f"{col}{tr}", f"=SUM({col}{first}:{col}{last})", fmt=KM2 if col != "B" else "0", bold=True)
    put(ws, f"F{tr}", f'=IF(N({TERR})>0,E{tr}/{TERR},"")', fmt=PCT, bold=True)
    put(ws, f"K{tr}", f'=IF(N({MAR})>0,J{tr}/{MAR},"")', fmt=PCT, bold=True)
    for r in range(first, tr + 1):
        put(ws, f"G{r}", f'=IF($E${tr}>0,E{r}/$E${tr},"")', fmt=PCT, bold=(r == tr))
        put(ws, f"L{r}", f'=IF($J${tr}>0,J{r}/$J${tr},"")', fmt=PCT, bold=(r == tr))
    return tr


section(GV, 4, "A. IUCN governance types (A–D)", 12)
t1 = disagg_table(GV, 5, gov_groups, RG["AJ"])
section(GV, t1 + 2, "B. Detailed WDPA governance types (GOV_TYPE)", 12)
t2 = disagg_table(GV, t1 + 3, [g for g, _ in gov], RG["G"], extra_blank=True)
section(GV, t2 + 2, "C. Supplementary – IUCN protected area management categories (not one of the five metadata disaggregations; "
                    "useful for 'strict protection' reporting)", 12)
t3 = disagg_table(GV, t2 + 3, lists["B"][1], RG["F"])
note(GV, f"A{t3 + 1}", "Totals should equal Headline_3.1 register sums (C6:D7). Differences indicate sites with blank or non-standard codes.")
widths(GV, {"A": 52, **{CL(i): 15 for i in range(2, 13)}})
GV_TOTAL_ROW = t1

# ================================================================ MANAGEMENT EFFECTIVENESS
M = sheet("Mgmt_Effectiveness", "5B9BD5")
title(M, "7. Coverage by management effectiveness – PROVISIONAL",
      "The metadata states the methodology for this disaggregation is still under development (proposal: UNEP-WCMC, IUCN & JNCC 2023). "
      "Classes here use normalised PAME scores and thresholds set in Setup (B24–B26). Report as a national provisional estimate.")
section(M, 4, "A. Coverage by effectiveness class", 12)
classes = lists["J"][1]
tm = disagg_table(M, 5, classes, RG["AK"])
r0 = tm + 2
section(M, r0, "B. Assessment coverage (continuity with Aichi Target 11 PAME reporting / GD-PAME)", 12)
header(M, r0 + 1, 1, ["Metric", "Terrestrial", "Marine"], 30)
first_c, last_c = 6, 6 + len(classes) - 1
put(M, f"A{r0 + 2}", "% of PA+OECM area with a valid PAME assessment (High + Moderate + Low + no score)", "label", bold=True)
put(M, f"B{r0 + 2}", f'=IF(E{tm}>0,SUM(E{first_c}:E{first_c + 3})/E{tm},"")', "key", PCT)
put(M, f"C{r0 + 2}", f'=IF(J{tm}>0,SUM(J{first_c}:J{first_c + 3})/J{tm},"")', "key", PCT)
put(M, f"A{r0 + 3}", "% of realm covered by PAs/OECMs assessed as effective (High + Moderate)", "label", bold=True)
put(M, f"B{r0 + 3}", f'=IF(N({TERR})>0,SUM(E{first_c}:E{first_c + 1})/{TERR},"")', "key", PCT)
put(M, f"C{r0 + 3}", f'=IF(N({MAR})>0,SUM(J{first_c}:J{first_c + 1})/{MAR},"")', "key", PCT)
note(M, f"A{r0 + 5}", "Related complementary indicators: MEPCA, R-METT, % of Biosphere Reserves with positive conservation outcome and effective management. "
                      "Report PAME results to GD-PAME (protectedplanet.net).")
widths(M, {"A": 60, **{CL(i): 15 for i in range(2, 13)}})

# ================================================================ TIME SERIES
T = sheet("Time_Series", "70AD47")
title(T, "8. Time series of coverage (cumulative by STATUS_YR)",
      "Missing designation years: metadata assigns each such site a random year drawn from another PA in the same country, repeated 1,000 times, and plots the median. "
      "Here the analytical expected value of that procedure is used: area of undated sites × share of dated sites designated by year t.")
header(T, 4, 1, ["Year", "Share of dated PAs designated by year (F_PA)", "Share of dated OECMs designated by year (F_OECM)",
                 "Terrestrial PA (km²)", "Terrestrial OECM (km²)", "Terrestrial coverage (%)", "Marine PA (km²)", "Marine OECM (km²)",
                 "Marine coverage (%)", "Terrestrial % – dated sites only (lower bound)", "Marine % – dated sites only (lower bound)"], 70)
T0, TN = 5, 5 + 200
for i, r in enumerate(range(T0, TN + 1)):
    yr = f"A{r}"
    put(T, yr, f'=IF({SET[27]}+{i}>{YEAR},"",{SET[27]}+{i})', fmt="0")
    g = f'=IF({yr}="","",'
    for col, typ in (("B", "PA"), ("C", "OECM")):
        put(T, f"{col}{r}", g + f'COUNTIFS({INC},1,{TYP},"{typ}",{YR},">0",{YR},"<="&{yr})/MAX(1,COUNTIFS({INC},1,{TYP},"{typ}",{YR},">0")))', fmt="0.000")
    for col, area, typ, fcol in (("D", TER, "PA", "B"), ("E", TER, "OECM", "C"), ("G", MRN, "PA", "B"), ("H", MRN, "OECM", "C")):
        put(T, f"{col}{r}", g + f'SUMIFS({area},{INC},1,{TYP},"{typ}",{YR},">0",{YR},"<="&{yr})+SUMIFS({area},{INC},1,{TYP},"{typ}",{YR},0)*{fcol}{r})', fmt=KM2)
    put(T, f"F{r}", g + f'IF(N({TERR})>0,(D{r}+E{r})/{TERR},""))', "calc", PCT)
    put(T, f"I{r}", g + f'IF(N({MAR})>0,(G{r}+H{r})/{MAR},""))', "calc", PCT)
    put(T, f"J{r}", g + f'IF(N({TERR})>0,SUMIFS({TER},{INC},1,{YR},">0",{YR},"<="&{yr})/{TERR},""))', fmt=PCT)
    put(T, f"K{r}", g + f'IF(N({MAR})>0,SUMIFS({MRN},{INC},1,{YR},">0",{YR},"<="&{yr})/{MAR},""))', fmt=PCT)
widths(T, {"A": 8, **{CL(i): 16 for i in range(2, 12)}})
T.freeze_panes = "B5"
note(T, "M5", "Notes:")
for i, t in enumerate([
    "• Uses register areas (not the Setup GIS override). The final year should match Headline_3.1 when no override is used.",
    "• Exact only if overlapping areas were attributed to the earliest-designated site during flattening (Setup B17).",
    "• Degazetted/downsized sites are not captured unless entered with their own history (known WDPA limitation).",
    "• The expected value equals the mean of the 1,000-draw Monte-Carlo; with many sites, mean ≈ median.",
]):
    note(T, f"M{6 + i}", t)

# ================================================================ QC
Q = sheet("QC_Checks", "FF0000")
title(Q, "9. Quality-control and method-compliance checks", "Resolve every WARN before reporting. INFO rows document known limitations.")
header(Q, 4, 1, ["#", "Check", "Value", "Result", "What to do"], 30)
checks = [
    ("Realm areas entered in Setup", f'=IF(N({TERR})>0,IF(N({MAR})>0,"Both","Terrestrial only"),"No")', '=IF(C{r}="No","WARN","PASS")', "Enter the terrestrial denominator (Setup B10) and the marine one (B11) unless the country is landlocked (enter 0)."),
    ("PA layer flattened (Setup B14)", f"={SET[14]}", '=IF(C{r}="Y","PASS","WARN")', "Dissolve overlapping PAs before computing areas (method step 4)."),
    ("OECMs: PA overlap erased (Setup B15)", f"={SET[15]}", '=IF(C{r}="Y","PASS","WARN")', "Erase OECM areas overlapping PAs, then flatten (OECM step 4)."),
    ("Mollweide equal-area projection (Setup B16)", f"={SET[16]}", '=IF(C{r}="Y","PASS","WARN")', "Recompute areas in an equal-area projection (step 6)."),
    ("Included sites without flattened net area", "=Headline_3.1!D26", '=IF(C{r}=0,"PASS","WARN")', "Enter net areas (register R–S) or GIS totals in Setup; otherwise the result is an upper bound."),
    ("Terrestrial PA+OECM area ≤ terrestrial realm", "=Headline_3.1!J6", '=IF(C{r}="","WARN",IF(C{r}<=1,"PASS","WARN"))', "Coverage >100%: check units (km² vs ha), denominators and double counting."),
    ("Marine PA+OECM area ≤ marine realm", "=Headline_3.1!J7", f'=IF(C{{r}}="",IF(N({MAR})=0,"PASS","WARN"),IF(C{{r}}<=1,"PASS","WARN"))', "As above (PASS automatically for landlocked countries)."),
    ("Register vs GIS override – terrestrial difference (%)", f'=IF(ISNUMBER({SET[18]}),IFERROR((Headline_3.1!C6+Headline_3.1!D6)/(N({SET[18]})+N({SET[19]}))-1,""),"")',
     '=IF(C{r}="","PASS",IF(ABS(C{r})<=0.01,"PASS","WARN"))', "If >1%, sites are missing from the register or net areas are inconsistent."),
    ("Register vs GIS override – marine difference (%)", f'=IF(ISNUMBER({SET[20]}),IFERROR((Headline_3.1!C7+Headline_3.1!D7)/(N({SET[20]})+N({SET[21]}))-1,""),"")',
     '=IF(C{r}="","PASS",IF(ABS(C{r})<=0.01,"PASS","WARN"))', "As above."),
    ("Included sites with any QC flag", f'=COUNTIFS({INC},1,{RG["AL"]},"?*")', '=IF(C{r}=0,"PASS","WARN")', "Filter register column AL and resolve each flag."),
    ("Included sites with STATUS_YR missing", "=Headline_3.1!D27", '=IF(C{r}=0,"PASS","INFO")', "Imputed in the time series (metadata method). Obtain dates where possible."),
    ("Included point (buffered) sites", "=Headline_3.1!D25", '=IF(C{r}=0,"PASS","INFO")', "Buffered circles may over- or under-estimate coverage; obtain boundaries."),
    ("Share of included area with GOV_TYPE not reported", f'=IFERROR((Governance!E{5 + len(gov_groups)}+Governance!J{5 + len(gov_groups)})/(Governance!E{GV_TOTAL_ROW}+Governance!J{GV_TOTAL_ROW}),"")',
     '=IF(C{r}="","PASS",IF(C{r}<=0.05,"PASS","WARN"))', "Complete GOV_TYPE – needed for the governance disaggregation."),
    ("Governance table total = headline register total", f'=ROUND(Governance!E{GV_TOTAL_ROW}+Governance!J{GV_TOTAL_ROW}-(Headline_3.1!C6+Headline_3.1!D6+Headline_3.1!C7+Headline_3.1!D7),3)',
     '=IF(C{r}=0,"PASS","WARN")', "Non-standard GOV_TYPE values – use the drop-down list."),
    ("KBAs with covered area > KBA area", f'=COUNTIFS(KBA_Coverage!$P${K0}:$P${KN},"Covered*")', '=IF(C{r}=0,"PASS","WARN")', "Use the flattened, PA-erased layers when intersecting KBAs."),
    ("KBAs without realm", f'=COUNTIFS(KBA_Coverage!$P${K0}:$P${KN},"*No realm*")', '=IF(C{r}=0,"PASS","WARN")', "Assign terrestrial / freshwater / ocean fraction."),
    ("Ecosystem units with coverage >100%", f'=COUNTIFS(Ecosystems!$L${B0}:$L${BN},"Covered*")+COUNTIFS(Ecosystems!$L${D0}:$L${DN},"Covered*")', '=IF(C{r}=0,"PASS","WARN")', "Check ecosystem extents and overlaps."),
    ("Example (fictional) data still present", f'=COUNTIFS(PA_OECM_Register!$B${N0}:$B${NN},"EXAMPLE*")+COUNTIFS(KBA_Coverage!$B${K0}:$B${KN},"EXAMPLE*")',
     '=IF(C{r}=0,"PASS","WARN")', "Delete orange example rows (register, KBA, Ecosystems, Setup) before reporting."),
    ("Known limitation – non-state governed sites under-represented", "—", '="INFO"', "Engage private/IPLC governance authorities to report sites (metadata limitation)."),
    ("Known limitation – lag between designation and database reporting", "—", '="INFO"', "Record dataset release month in Setup B7."),
]
for i, (lab, val, res, todo) in enumerate(checks):
    r = 5 + i
    put(Q, f"A{r}", i + 1, "label")
    put(Q, f"B{r}", lab, "label", bold=True)
    put(Q, f"C{r}", val, fmt="0.0%" if "%" in lab or "Share" in lab or "≤" in lab else None)
    put(Q, f"D{r}", res.format(r=r), bold=True)
    put(Q, f"E{r}", todo, "label")
QN = 5 + len(checks) - 1
Q.conditional_formatting.add(f"D5:D{QN}", CellIsRule(operator="equal", formula=['"PASS"'], fill=PatternFill("solid", fgColor="C6EFCE")))
Q.conditional_formatting.add(f"D5:D{QN}", CellIsRule(operator="equal", formula=['"WARN"'], fill=PatternFill("solid", fgColor="FFC7CE")))
Q.conditional_formatting.add(f"D5:D{QN}", CellIsRule(operator="equal", formula=['"INFO"'], fill=PatternFill("solid", fgColor="FFEB9C")))
put(Q, f"B{QN + 2}", "Number of WARN", "label", bold=True)
put(Q, f"C{QN + 2}", f'=COUNTIF(D5:D{QN},"WARN")', "key", "0")
widths(Q, {"A": 5, "B": 58, "C": 14, "D": 10, "E": 90})

# ================================================================ DASHBOARD
DB = sheet("Dashboard", "00B050")
title(DB, "10. Dashboard – GBF Headline Indicator 3.1")
put(DB, "A3", "=Setup!B4&\" (\"&Setup!B5&\") – reporting year \"&Setup!B6&\" – data: \"&Setup!B7", "label", bold=True)
header(DB, 5, 1, ["Headline figure", "Terrestrial & inland waters", "Marine & coastal"], 30)
kp = [("Coverage by PAs + OECMs (Indicator 3.1)", "J", PCT, True), ("of which PAs", "H", PCT, False),
      ("of which OECMs", "I", PCT, False), ("Target", "K", PCT, False), ("Gap to target (percentage points)", "L", "0.0", False),
      ("Additional area needed (km²)", "M", KM2, False), ("Status", "N", None, False)]
for i, (lab, col, fmt, key) in enumerate(kp):
    r = 6 + i
    put(DB, f"A{r}", lab, "label", bold=True)
    put(DB, f"B{r}", f"=Headline_3.1!{col}6", "key" if key else "calc", fmt)
    put(DB, f"C{r}", f"=Headline_3.1!{col}7", "key" if key else "calc", fmt)
header(DB, 14, 1, ["Disaggregation", "Value", "Note"], 30)
dash2 = [
    ("Inland waters – rivers (length covered)", "=Headline_3.1!G17", PCT, "RiverATLAS / national hydrography"),
    ("Inland waters – lakes & wetlands", "=Headline_3.1!G18", PCT, "GLWD v2 / national data"),
    ("Mean % of KBAs covered (all)", "=KBA_Coverage!D6", PCT, "SDG 14.5.1 / 15.1.2 / 15.4.1 family"),
    ("Mean % terrestrial KBAs covered", "=KBA_Coverage!D7", PCT, "SDG 15.1.2"),
    ("Mean % freshwater KBAs covered", "=KBA_Coverage!D8", PCT, "SDG 15.1.2"),
    ("Mean % marine KBAs covered", "=KBA_Coverage!D9", PCT, "SDG 14.5.1"),
    ("Mean % mountain KBAs covered", "=KBA_Coverage!D10", PCT, "SDG 15.4.1"),
    ("GET biomes assessed / ≥ target", '=Ecosystems!B35&" / "&Ecosystems!B36', None, "Representativeness"),
    ("Terrestrial coverage governed by IPs & LCs", f"=Governance!F{5 + 4}", PCT, "IUCN governance type D"),
    ("Marine coverage governed by IPs & LCs", f"=Governance!K{5 + 4}", PCT, "IUCN governance type D"),
    ("PA+OECM area with valid PAME (terrestrial)", f"=Mgmt_Effectiveness!B{r0 + 2}", PCT, "PROVISIONAL"),
    ("Quality-control warnings", f"=QC_Checks!C{QN + 2}", "0", "Must be 0 for an official figure"),
]
for i, (lab, fm, fmt, nt) in enumerate(dash2):
    r = 15 + i
    put(DB, f"A{r}", lab, "label", bold=True)
    put(DB, f"B{r}", fm, "calc", fmt)
    put(DB, f"C{r}", nt, "label")
widths(DB, {"A": 46, "B": 26, "C": 34})

ch = BarChart()
ch.type = "col"
ch.grouping = "stacked"
ch.overlap = 100
ch.title = "Coverage by realm: PAs and OECMs"
ch.y_axis.title = "% of realm area"
ch.y_axis.numFmt = "0%"
ch.y_axis.scaling.min = 0
ch.add_data(Reference(H, min_col=8, max_col=9, min_row=5, max_row=7), titles_from_data=True)
ch.set_categories(Reference(H, min_col=1, min_row=6, max_row=7))
ch.height, ch.width = 8, 14
DB.add_chart(ch, "E5")

lc = LineChart()
lc.title = "Coverage over time (expected value with imputed years)"
lc.y_axis.title = "% of realm area"
lc.y_axis.numFmt = "0%"
lc.add_data(Reference(T, min_col=6, min_row=4, max_row=TN), titles_from_data=True)
lc.add_data(Reference(T, min_col=9, min_row=4, max_row=TN), titles_from_data=True)
lc.set_categories(Reference(T, min_col=1, min_row=T0, max_row=TN))
lc.height, lc.width = 8, 14
DB.add_chart(lc, "E22")

# ================================================================ METADATA
MD = sheet("Metadata", "808080")
title(MD, "11. Summary of the official metadata – Headline Indicator 3.1",
      "Source: gbf-indicators.org/metadata/headline/3-1 (metadata last updated 1 September 2024). Custodians: UNEP-WCMC, IUCN, BirdLife International.")
md = [
    ("IDENTIFICATION", None),
    ("Indicator", "3.1 Coverage of protected areas and other effective area-based conservation measures"),
    ("Goal / Target", "KMGBF Target 3: ensure and enable that by 2030 at least 30 per cent of terrestrial and inland water areas, and of marine and coastal areas, especially areas of "
     "particular importance for biodiversity and ecosystem functions and services, are effectively conserved and managed through ecologically representative, well-connected and "
     "equitably governed systems of protected areas and OECMs, recognizing indigenous and traditional territories, where applicable."),
    ("Definition", "The percentage area covered by protected areas or OECMs, with five disaggregations: PA vs OECM; realm/biome/ecosystem; KBAs; management effectiveness; governance type."),
    ("Unit", "Percentage (%) of the realm area (terrestrial & inland waters; marine & coastal)."),
    ("CONCEPTS", None),
    ("Protected area", "A clearly defined geographical space, recognised, dedicated and managed, through legal or other effective means, to achieve the long-term conservation of nature "
     "with associated ecosystem services and cultural values (Dudley 2008)."),
    ("OECM", "A geographically defined area other than a Protected Area, which is governed and managed in ways that achieve positive and sustained long-term outcomes for the in situ "
     "conservation of biodiversity, with associated ecosystem functions and services and where applicable, cultural, spiritual, socio-economic, and other locally relevant values "
     "(CBD Decision 14/8)."),
    ("Areas of particular importance", "Sites holding significant populations/extents of threatened or geographically restricted species or ecosystems, or showing significant ecological "
     "integrity or irreplaceability; KBAs are the main operational proxy."),
    ("Key Biodiversity Area", "Sites contributing significantly to the global persistence of biodiversity, identified nationally through multi-stakeholder processes using the "
     "Global Standard for the Identification of KBAs (IUCN 2016)."),
    ("METHOD – PROTECTED AREAS", None),
    ("Step 1", "Filter WDPA: remove proposed sites, sites with status not reported, points with no reported area, and (most) UNESCO-MAB Biosphere Reserves."),
    ("Step 2", "Buffer point locations to a circle with area equal to the reported area."),
    ("Step 3", "Combine polygons and buffered points."),
    ("Step 4", "Flatten (dissolve) to remove overlaps and avoid double counting."),
    ("Step 5", "Intersect with base map (EEZ + land boundaries)."),
    ("Step 6", "Project to Mollweide equal-area."),
    ("Step 7", "Coverage = PA area (km²) ÷ realm area (km²)."),
    ("METHOD – OECMs", None),
    ("OECM steps", "Latest WD-OECM → buffer points → combine → ERASE areas overlapping PAs → flatten → intersect base map → Mollweide → coverage. "
     "Combined coverage = PA statistics + OECM statistics (no double counting because overlaps were erased)."),
    ("Realm formulas", "Terrestrial coverage = (terrestrial PA area + terrestrial OECM area) / terrestrial area. "
     "Marine coverage = (marine PA area + marine OECM area) / marine & coastal area."),
    ("KBA coverage", "Mean percentage of each KBA currently recognised that is covered by PAs and/or OECMs. KBA with ≥5% ocean overlap = marine. Sites may belong to several realms."),
    ("Time series", "Missing designation years: random year from another PA in the same country, 1,000 repetitions, median plotted. Global series 1819–present."),
    ("Ecosystems", "National approach: match ecosystem maps to the Global Ecosystem Typology; assess coverage; exclude inappropriate groups; aggregate EFGs to biomes; "
     "inland waters as river length and lake/wetland area covered. Ecoregions: Dinerstein et al. 2017 (terrestrial), Abell et al. 2008 (freshwater), Spalding et al. 2007/2012 (marine)."),
    ("Management effectiveness", "Methodology under development: groups areas by governance, outcomes, design/planning and management-effectiveness assessments (UNEP-WCMC, IUCN & JNCC 2023)."),
    ("Governance", "IUCN governance types: government; shared; private; Indigenous peoples and local communities. Proxy for 'equitably governed'."),
    ("Indigenous & traditional territories", "Not added as a third category. Counted only when they are PAs/OECMs (disaggregated by IPLC governance). "
     "Complementary indicator: extent of IPLC lands."),
    ("DATA SOURCES", None),
    ("Data", "WDPA and WD-OECM (UNEP-WCMC/IUCN, Protected Planet, monthly); World Database of KBAs (BirdLife International for the KBA Partnership); GET maps; RiverATLAS; GLWD v2; "
     "base maps: EEZ (VLIZ), World Vector Shoreline, GADM."),
    ("Data provision", "Data submitted by national governments or governance authorities, verified by UNEP-WCMC; quality controls and manual resolution of discrepancies."),
    ("Release", "Monthly (headline, PA/OECM, realm) on Protected Planet; annual (KBA – SDG database, IBAT); biennial Protected Planet Report (ecoregion, biome, governance, trends)."),
    ("LIMITATIONS", None),
    ("Protected areas", "Non-state governed sites under-represented; some designation dates unknown; most countries have not yet reported OECMs; lag between designation and reporting; "
     "degazettement not comprehensively documented; buffered points over/under-estimate coverage."),
    ("KBAs", "Historic bias toward birds (IBAs), now <50% of KBA trigger species; focus on highly threatened species (AZE); taxonomic and ecosystem coverage incomplete."),
    ("Coverage ≠ effectiveness", "Area coverage does not by itself show effective conservation, connectivity or equity – hence the disaggregations and complementary indicators "
     "(e.g. ProtConn, MEPCA, R-METT, KBA status)."),
    ("Related indicators", "SDG 14.5.1, 15.1.2, 15.4.1; complementary: status of KBAs; PA/OECM coverage of KBAs important for migratory species; MEPCA; R-METT; "
     "% of Biosphere Reserves with positive conservation outcomes; ProtConn; extent of IPLC lands."),
    ("Contact", "UNEP-WCMC (Protected Planet team) – see metadata page for current contact."),
]
r = 4
for k, v in md:
    if v is None:
        section(MD, r, k, 2)
    else:
        put(MD, f"A{r}", k, "label", bold=True)
        put(MD, f"B{r}", v, "label")
        MD.row_dimensions[r].height = max(15, 14 * (len(v) // 130 + 1))
    r += 1
widths(MD, {"A": 30, "B": 150})

# ================================================================ REFERENCES
RF = sheet("References", "808080")
title(RF, "References")
refs = [
    "CBD (2022). Decision 15/4 Kunming-Montreal Global Biodiversity Framework; Decision 15/5 Monitoring framework. Montreal: Secretariat of the CBD.",
    "CBD (2018). Decision 14/8 Protected areas and other effective area-based conservation measures.",
    "GBF Indicators – Metadata for Headline Indicator 3.1. https://www.gbf-indicators.org/metadata/headline/3-1 (updated 1 Sept 2024).",
    "Dudley, N. (ed.) (2008). Guidelines for Applying Protected Area Management Categories. Gland: IUCN.",
    "IUCN-WCPA Task Force on OECMs (2019). Recognising and reporting other effective area-based conservation measures. Gland: IUCN.",
    "Borrini-Feyerabend, G. et al. (2013). Governance of Protected Areas: From understanding to action. Best Practice PA Guidelines Series No. 20. Gland: IUCN.",
    "IUCN (2016). A Global Standard for the Identification of Key Biodiversity Areas, Version 1.0. Gland: IUCN.",
    "Butchart, S.H.M. et al. (2012). Protecting important sites for biodiversity contributes to meeting global conservation targets. PLoS ONE 7(3): e32529.",
    "Butchart, S.H.M. et al. (2015). Shortfalls and solutions for meeting national and global conservation area targets. Conservation Letters 8(5): 329–337.",
    "Keith, D.A. et al. (2022). A function-based typology for Earth's ecosystems. Nature 610: 513–518. (IUCN Global Ecosystem Typology, https://global-ecosystems.org)",
    "Dinerstein, E. et al. (2017). An ecoregion-based approach to protecting half the terrestrial realm. BioScience 67(6): 534–545.",
    "Abell, R. et al. (2008). Freshwater ecoregions of the world. BioScience 58(5): 403–414.",
    "Spalding, M.D. et al. (2007). Marine ecoregions of the world. BioScience 57(7): 573–583.",
    "Spalding, M.D. et al. (2012). Pelagic provinces of the world. Ocean & Coastal Management 60: 19–30.",
    "Linke, S. et al. (2019). Global hydro-environmental sub-basin and river reach characteristics at high spatial resolution (RiverATLAS). Scientific Data 6: 283.",
    "Lehner, B. et al. (2024). Global Lakes and Wetlands Database (GLWD) version 2.",
    "Visconti, P. et al. (2013). Effects of errors and gaps in spatial data sets on assessment of conservation progress. Conservation Biology 27(5): 1000–1010.",
    "Plumptre, A.J. et al. (2024). Targeting site conservation to increase the effectiveness of new global biodiversity targets. One Earth 7(1): 11–17.",
    "UNEP-WCMC, IUCN & JNCC (2023). Proposed methodology for disaggregating coverage of PAs and OECMs by management effectiveness (cited in metadata).",
    "UNEP-WCMC & IUCN (2024). Protected Planet Report 2024. Cambridge & Gland. https://www.protectedplanet.net",
    "UNEP-WCMC (2019 and later). User Manual for the World Database on Protected Areas and World Database on OECMs. Cambridge: UNEP-WCMC.",
    "Protected Planet – Calculating protected area coverage. https://www.protectedplanet.net/c/calculating-protected-area-coverage",
]
for i, t in enumerate(refs):
    put(RF, f"A{3 + i}", t, "label")
widths(RF, {"A": 170})

# order sheets
order = ["ReadMe", "Setup", "PA_OECM_Register", "Headline_3.1", "Ecosystems", "KBA_Coverage", "Governance",
         "Mgmt_Effectiveness", "Time_Series", "QC_Checks", "Dashboard", "Metadata", "References", "Lists"]
wb._sheets = [wb[n] for n in order]
wb.active = 0
for ws in wb.worksheets:
    for row in ws.iter_rows():
        for c in row:
            if c.value is not None and (c.font is None or c.font.name != F):
                c.font = Font(name=F, size=c.font.size or 10, bold=c.font.bold, italic=c.font.italic, color=c.font.color)
wb.save(OUT)
print("saved", OUT)
