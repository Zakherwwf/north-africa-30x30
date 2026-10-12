# Algeria – GBF Headline Indicator 3.1 (30×30) worked example

Everything needed to reproduce Algeria's Indicator 3.1 figures with the Excel tool, from raw data to report.

**Results (WDPA/WD-OECM October 2026, Mollweide equal-area)**
- Land: protected areas 107,763.96 km² (**4.65%**) + OECMs, protected-area overlap removed, 1,151,696.35 km² (**49.67%**) = **54.32%** of 2,318,644 km². Target met, through the five Cultural Parks reported as OECMs.
- Sea: 89.78 / 131,439.54 km² = **0.07%**. Gap to 30%: 39,342 km²; to the national 5% target: 6,482 km².
- Protected Planet (Oct 2026): 4.66% PA, 54.41% PA+OECM, 0.07% sea. 7th National Report (2026): Cultural Parks 43.77% of the territory (legal areas).
- KBAs (65 polygons, Sept 2026): mean 43.5% covered (35.1% by PAs alone); 17 complete, 22 partial, 26 none. Mountain KBAs 22.7% (42 KBAs).
- Inland waters: 48.2% of lakes and wetlands (GLWD v2) and 53.2% of river length lie in PAs or OECMs.

## Folders
| Folder | Content |
|---|---|
| `01_data/wdpa/` | WDPA polygons (71) and points (2), WD-OECM polygons (5): `.shp`, `.geojson`, `WDPA_WDOECM_DZA.gpkg` |
| `01_data/boundaries/` | geoBoundaries ADM0, Marine Regions EEZ v12 |
| `01_data/kba/` | Official KBA polygons and points for Algeria (licensed – do not republish), trigger species, 67 factsheet pages and table |
| `01_data/ecoregions/`, `marine_ecoregions/`, `mountains/`, `inland_waters/` | RESOLVE 2017, MEOW, GMBA v2.0, HydroRIVERS and GLWD v2 clipped to Algeria |
| `01_data/protected_planet/` | Country page, statistics JSON (PA and PA+OECM), GD-PAME by site, 78 site pages |
| `02_documents/` | Algeria's CBD national reports (4th, 5th, 6th, 7th 2026), NBSAP 2016–2030 and 2025, CBD country profile, plus the method documents (GBF 3.1 metadata, decisions 14/8, 15/4, 15/5, 16/31, SDG metadata, WDPA/WDPCA manuals, IUCN guidelines, KBA standard and metadata, GLWD and HydroRIVERS docs) |
| `03_analysis/scripts/` | Country-generic pipeline driven by `country.json` |
| `03_analysis/outputs/` | Flat PA and OECM layers, per-site net areas, overlaps, KBA coverage and gap layers, ecosystem and wetland tables, tool config |
| `04_tool/` | `GBF_3.1_Tool_Algeria_Worked_Example.xlsx` – filled tool, recalculated in Excel with zero formula errors |
| `05_guide/` | `Algeria_Indicator_3.1_Guide.html` – 14-step illustrated walkthrough |

## Running the pipeline
Python with geopandas, shapely ≥ 2, pyproj, rasterio, openpyxl. Settings (country code, global source paths, effectiveness transfers, biome crosswalk) are in `03_analysis/scripts/country.json`.
```
python 00_prepare_layers.py   # clip ecoregions, MEOW, HydroRIVERS, GMBA to the country
python 01_gis_flatten.py      # base map, filter, buffer, clip, flatten PAs, erase PAs from OECMs, net areas
python 02_kba_overlay.py      # KBA polygons vs PA and OECM layers
python 03_wetlands_glwd.py    # GLWD v2 lakes and wetlands
python 04_make_config.py      # register, KBA, ecosystem and inland-water rows
TOOL_CFG=../outputs/tool_config_algeria.json python 05_build_tool.py
python 06_make_guide.py
```
The global source files are not duplicated: `country.json` points to the copies in `../tunisia/01_data/*/_global_download/` and to the global KBA file in `../KBAs/KBA_Data/`. Keep those folders, or change the paths.

## Method choices to record in the national report
- The five Cultural Parks are counted as OECMs because Algeria reported them to the WD-OECM; their OECM status against CBD decision 14/8 should be documented nationally. PA and OECM figures are reported separately.
- OECM area is measured after erasing all protected-area area (metadata OECM step 4); per-site net areas give PAs precedence, then the earliest designation.
- Coastal gaps between the land outline and the EEZ (47 km²) are assigned to the marine realm.
- KBA realm rules: marine if ≥ 5% of the polygon is outside land; terrestrial if ≥ 5% on land; mountain if ≥ 5% inside GMBA v2.0; freshwater from the factsheet system, site name or freshwater trigger species. Two KBA points without area are not measured.
- Lakes and wetlands = GLWD v2 classes 1–3, 6 and 8–32 on land; river channels and rice paddies excluded.
- BREMi evaluations on excluded biosphere-reserve records are moved to the national park / World Heritage record of the same site (register column Y).
