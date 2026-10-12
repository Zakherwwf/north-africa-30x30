# Morocco – GBF Headline Indicator 3.1 (30×30) worked example

Everything needed to reproduce Morocco's Indicator 3.1 figures with the Excel tool, from raw data to report.

**Results (WDPA/WD-OECM October 2026, Mollweide equal-area, Western Sahara excluded)**
- Land: protected areas 8,849.13 km² (**2.13%**) + OECMs, protected-area overlap removed, 131,066.07 km² (**31.56%**) = **33.70%** of 415,235 km². Target met, through 221 permanent hunting reserves (29.7 points) and 117 SIBEs (1.9 points) reported as OECMs.
- Sea: 918.51 / 281,295 km² = **0.33%** (PAs 0.28%, OECMs 0.04%). Gap to 30%: 83,470 km².
- Protected Planet (Oct 2026): 2.14% PA, 33.75% PA+OECM, 0.31% sea. 7th National Report (2026): 24.2% (national data set, 2025).
- KBAs (64 polygons + 3 buffered points): mean 58.5% covered (24.2% by PAs alone); 18 complete, 45 partial, 4 none.
- Governance: 88.1% of covered land under shared (collaborative) governance. No current effectiveness evaluation.
- Inland waters: 21.6% of lakes and wetlands (GLWD v2) and 34.8% of river length in PAs or OECMs.

## Western Sahara
geoBoundaries' MAR outline includes Western Sahara; Protected Planet, the Marine Regions EEZ and the WDPA keep it separate. Land is therefore
`geoBoundaries-MAR-ADM0_incl_Western_Sahara.geojson` clipped north of 27°40'N (`geoBoundaries-MAR-ADM0.geojson`, 415,235 km² vs Protected Planet 414,105 km²).
The sea is the Marine Regions "Moroccan EEZ"; the Western Sahara overlapping-claim zone is kept for reference only. Six KBAs centred south of 27°40'N are in
`01_data/kba/KBA_Western_Sahara_excluded.gpkg` and not counted. Including Western Sahara would give 685,174 km² of land and about 20% land coverage.

## Folders
| Folder | Content |
|---|---|
| `01_data/wdpa/` | WDPA polygons (91) and WD-OECM polygons (338): `.shp`, `.geojson`, `WDPA_WDOECM_MAR.gpkg` |
| `01_data/boundaries/` | geoBoundaries ADM0 (with and without Western Sahara), Marine Regions EEZ v12 and the Western Sahara overlapping-claim zone |
| `01_data/kba/` | Official KBA polygons and points for Morocco (licensed – do not republish), excluded Western Sahara KBAs, trigger species, 67 factsheets |
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
- Western Sahara excluded from land, sea and KBAs (see above).
- Hunting reserves and SIBEs counted as OECMs because Morocco reported them to the WD-OECM; their status against CBD decision 14/8 should be documented. PA and OECM figures reported separately.
- 42 proposed protected areas (11,064 km², incl. the new natural parks) excluded until designated in the WDPA.
- KBA points with a reported area buffered to circles; KBA realm rules as for the other countries (5% thresholds; GMBA v2.0 for mountains).
- Al-Hoceima SPAMI IMET 2018 evaluation moved to Al Hoceima National Park (same physical park).
