# Tunisia – GBF Headline Indicator 3.1 (30×30) worked example

Everything needed to reproduce Tunisia's Indicator 3.1 figures with the Excel tool, from raw data to report.

**Results (WDPA October 2026, Mollweide equal-area)**
- Land: 12,344.57 / 155,616.70 km² = **7.93%**. Gap to 30%: 34,340 km².
- Sea: 1,068.35 / 99,981.97 km² = **1.07%**. Gap to 30%: 28,926 km².
- Protected Planet (Oct 2026): 7.91% / 1.11%. Tunisia 7th National Report (2026): 7.86% / 1.1%.
- Key Biodiversity Areas (72, official polygons Sept 2026): mean 41.3% covered; 2 complete, 48 partial, 22 not covered.
  Marine KBAs 32.1% (15), freshwater 39.4% (32), mountain 44.2% (13).
- Inland waters: 46.8% of lake and wetland area (5,725 of 12,240 km², GLWD v2) and 9.8% of river length (3,717 of 37,829 km) lie in protected areas.

## 01_data – raw inputs
| Folder | Content | Source |
|---|---|---|
| `wdpa/` | WDPA polygons (137) and points (12): `.shp`, `.geojson`, `WDPA_WDOECM_TUN.gpkg`. No OECMs reported. | UNEP-WCMC WDPA map service, Oct 2026 |
| `boundaries/` | geoBoundaries ADM0 (land), Marine Regions EEZ v12 (sea) | geoboundaries.org; marineregions.org |
| `kba/` | **Official KBA polygons for Tunisia** (`KBAsGlobal_2026_September_TUN_polygons.shp`, `KBA_TUN_2026_September.gpkg`), trigger species for the 72 KBAs, factsheet table and pages | World Database of KBAs, September 2026 (licensed – do not republish) |
| `mountains/` | GMBA Mountain Inventory v2.0 (standard) clipped to Tunisia (+ global zip) | Snethlage et al. 2022 |
| `ecoregions/` | RESOLVE Ecoregions 2017 clipped to Tunisia (+ global zip) | Dinerstein et al. 2017 |
| `marine_ecoregions/` | Marine Ecoregions of the World, clipped to the EEZ | Spalding et al. 2007 |
| `inland_waters/` | HydroRIVERS v1.0 clipped to Tunisia; `GLWD_v2_TUN/` – GLWD v2.0 per-class wetland area grids (ha×10) clipped to Tunisia (+ global zips) | hydrosheds.org; GLWD v2 (Lehner et al. 2025, figshare 10.6084/m9.figshare.28519994) |
| `protected_planet/` | Country page, statistics JSON, GD-PAME evaluations per site, 149 site pages | protectedplanet.net |

`_global_download/` folders hold the original global files (~1.9 GB, mostly the GLWD v2 zip); they can be deleted once the clips exist.

## 02_documents – reference documents
GBF 3.1 metadata; KMGBF decisions (COP15 15/4, 15/5; COP16 16/31; COP14 14/8 on OECMs; SBSTTA-24/3); SDG 14.5.1 and 15.1.2 metadata;
Protected Planet coverage method; WDPCA Manual 2.0 (EN), WDPA manual 1.6 (FR) and 1.5 (AR); Protected Planet data quick guide; PAME draft approach;
IUCN guidelines (governance, management categories, OECMs); KBA Global Standard; **KBA metadata and field definitions (September 2026)**;
Jonas et al. 2014; geoBoundaries paper; HydroRIVERS and GLWD v2 technical documentation; Tunisia's CBD national reports (3rd, 5th, 6th 2019, 7th 2026),
NBSAP/SPANB 2018–2030 and CBD country profile.

## 03_analysis
Run in order (Python with geopandas, shapely ≥ 2, pyproj, openpyxl):
1. `scripts/01_gis_flatten.py` – base map (land with inland waters filled; sea = EEZ + coastal lagoons), filter, buffer points, clip, Mollweide, dissolve, earliest-site overlap attribution, ecoregion and river overlays.
2. `scripts/02_kba_overlay.py` – KBA polygons vs the flat layer: area, ocean/land/mountain fractions, freshwater flag, covered area; unprotected KBA parts; foreign KBAs touching Tunisia.
3. `scripts/03_wetlands_glwd.py` – GLWD v2 lakes and wetlands (33 classes) vs the flat layer, fractional cell coverage on a 10×10 sub-grid.
4. `scripts/04_make_config.py` – register (149 rows), GD-PAME transfers, KBA rows, ecosystem and inland-water rows.
5. `scripts/05_build_tool.py` – builds the workbook: `TOOL_CFG=../outputs/tool_config_tunisia.json python 05_build_tool.py`.
6. `scripts/06_make_guide.py` – the illustrated HTML guide (style in `guide_style.css`).

Also needs `rasterio` for step 3.

Main outputs in `outputs/`: `PA_flattened_TUN_*` (flat PA layer), `base_map_realms_TUN.shp`, `PA_included_buffered_moll.gpkg`,
`sites_net_areas.csv`, `overlap_pairs.csv`, `KBA_coverage_TUN.shp` + `kba_coverage_TUN.csv`, `KBA_unprotected_parts_TUN.shp`,
`kba_foreign_overlapping_TUN.csv`, `glwd_wetland_coverage_by_class.csv`, `glwd_wetland_coverage_by_group.csv`, `glwd_results.json`, `ecoregion_coverage.csv`, `marine_ecoregion_coverage.csv`, `results.json`, `kba_results.json`, `tool_config_tunisia.json`.

## 04_tool
`GBF_3.1_Tool_Tunisia_Worked_Example.xlsx` – the filled tool, recalculated in Excel with zero formula errors.

## 05_guide
`Tunisia_Indicator_3.1_Guide.html` – 13-step illustrated walkthrough.

## Method choices to record in the national report
- Coastal lagoons lying between the land outline and the EEZ (113 km²) are assigned to the marine & coastal realm.
- KBA realm rules: marine if ≥ 5% of the polygon is outside land (metadata); terrestrial if ≥ 5% on land; mountain if ≥ 5% inside GMBA v2.0 (national choice);
  freshwater if the factsheet lists a freshwater system, the site is a dam/river/garaet/spring, or a trigger species is a freshwater fish, amphibian or dragonfly.
- Lakes and wetlands = GLWD v2 classes 1–3, 6 and 8–32 on land; river channels (4, 5, 7) are excluded because rivers are reported by length, and rice paddies (33) as anthropogenic.
- Ecoregion → IUCN GET biome crosswalk is approximate (T2/T3/T5). Marine biomes (shelf vs pelagic) are not computed.
- GD-PAME evaluations on World Heritage / biosphere-reserve records were moved to the national-park record that holds the area (register column Y).
