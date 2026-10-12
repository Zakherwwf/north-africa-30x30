# Egypt – GBF Headline Indicator 3.1 (30×30) worked example

Everything needed to reproduce Egypt's Indicator 3.1 figures with the Excel tool, from raw data to report.

**Results (WDPA October 2026, Mollweide equal-area, Halaib Triangle excluded)**
- Land: 110,805.44 / 986,014 km² = **11.24%**. Gap to 30%: 184,999 km²; to the national 20% target (NBSAP 2025): about 86,400 km².
- Sea: 8,821.17 / 243,974 km² = **3.62%**. Gap to 30%: 64,371 km².
- With Halaib included (`07_sensitivity_halaib.py`): 12.81% of land, 4.62% of sea.
- Protected Planet (Oct 2026): 13.12% / 5.07% (its protected area matches the Halaib-included figure, its base map the Halaib-excluded one).
- No OECMs. 13 proposed protected areas (56,941 km², incl. Qattara Depression) excluded.
- KBAs (33 polygons, 3 Halaib KBAs set aside): mean 35.2% covered; 8 complete, 10 partial, 15 none.
- Governance: 48% of covered land without GOV_TYPE (QC warning). One current effectiveness evaluation (Wadi Al-Hitan).
- Inland waters: 5.0% of lakes and wetlands (GLWD v2), 10.6% of river length.

## Halaib Triangle
geoBoundaries' EGY outline includes the Halaib Triangle (claimed by Egypt and Sudan). Land = `geoBoundaries-EGY-ADM0_incl_Halaib.geojson` minus
`Halaib_Triangle_EGY_SDN_overlap.geojson` (overlap of the geoBoundaries EGY and SDN outlines, 18,042 km²). Sea = Marine Regions "Egyptian EEZ";
the Halaib and Egypt/Libya overlapping-claim waters are in `MarineRegions_overlapping_claims_EGY.geojson`. KBAs Gebel Elba, Rawabel islands and Siyal
islands (in Halaib land or waters) are in `01_data/kba/KBA_Halaib_excluded.gpkg`.

## Folders
| Folder | Content |
|---|---|
| `01_data/wdpa/` | WDPA polygons (47) and points (3): `.shp`, `.geojson`, `WDPA_WDOECM_EGY.gpkg`. No OECMs |
| `01_data/boundaries/` | geoBoundaries ADM0 (with and without Halaib), Halaib polygon, Marine Regions EEZ v12 and overlapping-claim zones |
| `01_data/kba/` | Official KBA polygons for Egypt (licensed – do not republish), Halaib KBAs set aside, trigger species, factsheets |
| `01_data/ecoregions/`, `marine_ecoregions/`, `mountains/`, `inland_waters/` | RESOLVE 2017, MEOW, GMBA v2.0, HydroRIVERS and GLWD v2 clipped to Egypt |
| `01_data/protected_planet/` | Country page, statistics JSON, GD-PAME by site, 50 site pages |
| `02_documents/` | Egypt NBSAP 2015–2030 and NBSAP 2025, 5th National Report, CBD country profile, plus the method documents |
| `03_analysis/scripts/` | Country-generic pipeline (`country.json`) + `07_sensitivity_halaib.py` |
| `03_analysis/outputs/` | Flat PA layer, base-map realms, per-site net areas, overlaps, KBA coverage and gap layers, ecosystem and wetland tables, Halaib sensitivity, tool config |
| `04_tool/` | `GBF_3.1_Tool_Egypt_Worked_Example.xlsx` – filled tool, recalculated in Excel with zero formula errors |
| `05_guide/` | `Egypt_Indicator_3.1_Guide.html` – 13-step illustrated walkthrough |

## Running the pipeline
```
python 00_prepare_layers.py; python 01_gis_flatten.py; python 02_kba_overlay.py; python 03_wetlands_glwd.py; python 04_make_config.py
TOOL_CFG=../outputs/tool_config_egypt.json python 05_build_tool.py; python 06_make_guide.py; python 07_sensitivity_halaib.py
```
Global source files are read from `../tunisia/01_data/*/_global_download/` and `../KBAs/KBA_Data/` (paths in `country.json`).

## Method choices to record in the national report
- Halaib excluded from land, sea and KBAs in the main figures; Halaib-included figures given as a sensitivity.
- Ramsar points Lake Bardawil and Lake Burullus buffered to circles (the KBA database does not buffer points, hence its lower coverage for these KBAs).
- Biome crosswalk: the Nile Delta flooded savanna ecoregion (RESOLVE "Flooded Grasslands") is grouped with deserts (T5); treat T5 with care.
- Effectiveness transfers: Omayed and Wadi Allaqi BREMi → El Omayed and Wadi Al Alaqi; Wadi El Rayan Ramsar IBA monitoring → Wadi El Rayan protectorate.
