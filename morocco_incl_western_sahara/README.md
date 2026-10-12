# Morocco including Western Sahara – GBF Headline Indicator 3.1 (30×30) worked example

Second version of the `../morocco` example, with Western Sahara counted as part of Morocco (land, sea and KBAs). Same data, scripts and method; only the base map and the KBA set differ.

**Results (WDPA/WD-OECM October 2026, Mollweide equal-area, Western Sahara included)**
- Land: protected areas 8,849.41 km² (**1.29%**) + OECMs, protected-area overlap removed, 131,066.07 km² (**19.13%**) = **20.42%** of 685,174 km². Target not met: 65,637 km² (9.6 points) short of 30%.
- Sea: 918.51 / 566,673 km² = **0.16%** (PAs 0.14%, OECMs 0.02%). Gap to 30%: 169,083 km².
- KBAs (70 polygons + 3 buffered points): mean 53.7% covered (22.2% by PAs alone); 18 complete, 45 partial, 10 none (the six Western Sahara KBAs have no coverage).
- Inland waters: 19.6% of lakes and wetlands (GLWD v2) and 21.3% of river length in PAs or OECMs.
- Governance and effectiveness shares are unchanged from the `morocco` version (the covered area is the same).
- Without Western Sahara (the `morocco` folder, which matches Protected Planet): 33.70% land, 0.33% sea.

## What changed from `../morocco`
- `01_data/boundaries/geoBoundaries-MAR-ADM0.geojson` is now the full outline (copy of `..._incl_Western_Sahara.geojson`); the cut version is kept as `..._north_of_27d40N_original.geojson`.
- `01_data/boundaries/MarineRegions_EEZ_v12_MAR.geojson` is now the Moroccan EEZ plus the Western Sahara overlapping-claim zone (285,374 km²); the original is `..._MAR_only_original.geojson`.
- `01_data/kba/KBAsGlobal_2026_September_MAR_polygons.shp` includes the six KBAs from `KBA_Western_Sahara_excluded.gpkg` (Dakhla area, Baie d'Ad Dakhla, Pointe d'Awfist, Zone Humide de Laayoune, Canary current shelf 3, Canary current shelf-break (north)).
- No WDPA or WD-OECM record lies in Western Sahara (checked against the UNEP-WCMC service, October 2026, by ISO3 = ESH and by location), so the site register is unchanged; only 0.28 km² of Khnifiss National Park lies south of 27°40'N.
- `country.json` (boundary note), `04_make_config.py` (Setup row 9) and `06_make_guide.py` (figures and text) were updated; the other scripts are unchanged.
- The workbook in `04_tool/` was rebuilt with these figures.

## Folders
| Folder | Content |
|---|---|
| `01_data/wdpa/` | WDPA polygons (91) and WD-OECM polygons (338): `.shp`, `.geojson`, `WDPA_WDOECM_MAR.gpkg` |
| `01_data/boundaries/` | geoBoundaries ADM0 (with and without Western Sahara), Marine Regions EEZ v12 and the Western Sahara overlapping-claim zone |
| `01_data/kba/` | Official KBA polygons and points for Morocco including the six Western Sahara KBAs (licensed – do not republish), trigger species, 67 factsheets |
| `01_data/ecoregions/`, `marine_ecoregions/`, `mountains/`, `inland_waters/` | RESOLVE 2017, MEOW, GMBA v2.0, HydroRIVERS and GLWD v2 clipped to Morocco |
| `01_data/protected_planet/` | Country page, statistics JSON, GD-PAME by site, 429 site pages |
| `02_documents/` | Morocco's CBD national reports (4th, 5th, 7th 2026), NBSAP, CBD country profile, plus the method documents |
| `03_analysis/scripts/` | Country-generic pipeline driven by `country.json` (same code as Algeria) |
| `03_analysis/outputs/` | Flat PA and OECM layers, base-map realms, per-site net areas, overlaps, KBA coverage and gap layers, ecosystem and wetland tables, tool config |
| `04_tool/` | `GBF_3.1_Tool_Morocco_Worked_Example.xlsx` – filled tool, recalculated in Excel with zero formula errors |
| `05_guide/` | `Morocco_Indicator_3.1_Guide.html` – 14-step illustrated walkthrough |

## Running the pipeline
```
python 00_prepare_layers.py; python 01_gis_flatten.py; python 02_kba_overlay.py; python 03_wetlands_glwd.py; python 04_make_config.py
TOOL_CFG=../outputs/tool_config_morocco.json python 05_build_tool.py; python 06_make_guide.py
```
Global source files are read from `../tunisia/01_data/*/_global_download/` and `../KBAs/KBA_Data/` (paths in `country.json`).

## Method choices to record in the national report
- Western Sahara included in land, sea and KBAs (see above); percentages therefore differ from Protected Planet.
- Hunting reserves and SIBEs counted as OECMs because Morocco reported them to the WD-OECM; their status against CBD decision 14/8 should be documented. PA and OECM figures reported separately.
- 42 proposed protected areas (11,064 km², incl. the new natural parks) excluded until designated in the WDPA.
- KBA points with a reported area buffered to circles; KBA realm rules as for the other countries (5% thresholds; GMBA v2.0 for mountains).
- Al-Hoceima SPAMI IMET 2018 evaluation moved to Al Hoceima National Park (same physical park).
