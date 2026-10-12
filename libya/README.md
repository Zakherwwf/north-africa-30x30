# Libya – GBF Headline Indicator 3.1 (30×30) worked example

Everything needed to reproduce Libya's Indicator 3.1 figures with the Excel tool, from raw data to report.

**Results (WDPA October 2026, Mollweide equal-area)**
- Land: 2,099.33 / 1,630,170 km² = **0.13%**. Gap to 30%: 486,952 km².
- Sea: 2,241.06 / 357,323 km² = **0.63%**. Gap to 30%: 104,956 km².
- Protected Planet (Oct 2026): 0.13% / 0.63%. NBSAP 2023–2030: about 0.16% (11 reserves, 2010); 30 new sites announced in 2021, none in the WDPA.
- No OECMs. All 5 WDPA records are points, buffered to circles of their reported area; El Nagaza National Park (4,000 km²) gives 84% of the land figure and all of the sea figure.
- KBAs (18 polygons): mean 0.3% covered; 16 with no coverage. Lakes and wetlands 0.3%, rivers 0.1%.

## Folders
| Folder | Content |
|---|---|
| `01_data/wdpa/` | WDPA points (5): `.shp`, `.geojson`, `WDPA_WDOECM_LBY.gpkg`. No polygons, no OECMs |
| `01_data/boundaries/` | geoBoundaries ADM0, Marine Regions EEZ v12 (Libyan EEZ) and the Egypt/Libya overlapping-claim zone (reference only) |
| `01_data/kba/` | Official KBA polygons for Libya (licensed – do not republish), trigger species, 18 factsheets |
| `01_data/ecoregions/`, `marine_ecoregions/`, `mountains/`, `inland_waters/` | RESOLVE 2017, MEOW, GMBA v2.0, HydroRIVERS and GLWD v2 clipped to Libya |
| `01_data/protected_planet/` | Country page, statistics JSON, 5 site pages (no GD-PAME records) |
| `02_documents/` | Libya NBSAP 2023–2030, IUCN ToR for the inventory of marine and coastal sites, CBD country profile, plus the method documents. No CBD national report could be retrieved |
| `03_analysis/scripts/` | Country-generic pipeline driven by `country.json` |
| `03_analysis/outputs/` | Buffered PA layer, base-map realms, per-site net areas, KBA coverage and gap layers, ecosystem and wetland tables, tool config |
| `04_tool/` | `GBF_3.1_Tool_Libya_Worked_Example.xlsx` – filled tool, recalculated in Excel with zero formula errors |
| `05_guide/` | `Libya_Indicator_3.1_Guide.html` – 12-step illustrated walkthrough |

## Running the pipeline
```
python 00_prepare_layers.py; python 01_gis_flatten.py; python 02_kba_overlay.py; python 03_wetlands_glwd.py; python 04_make_config.py
TOOL_CFG=../outputs/tool_config_libya.json python 05_build_tool.py; python 06_make_guide.py
```
Global source files are read from `../tunisia/01_data/*/_global_download/` and `../KBAs/KBA_Data/` (paths in `country.json`).

## Method choices and caveats
- All sites are points: coverage is approximate and depends on the reported areas and coordinates. Real boundaries would change every figure.
- Sea = Libyan EEZ only, as in Protected Planet; the Egypt/Libya overlapping claim (8,114 km²) is not counted.
- The KBA database reports 0% for all Libyan KBAs because it does not buffer point-only protected areas; this workbook does, giving 2.8–2.9% for Nefhusa and Jabal al Akhdar.
