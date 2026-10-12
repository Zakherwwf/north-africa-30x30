# North Africa 30×30: GBF Headline Indicator 3.1

Worked examples of Headline Indicator 3.1 of the Kunming-Montreal Global Biodiversity Framework (coverage of protected areas and OECMs, Target 3 "30×30"). The examples cover Tunisia, Algeria, Morocco, Libya and Egypt, and include the Excel calculation tool, the analysis code, the outputs, step-by-step guides and a regional dashboard.

Data: WDPA / WD-OECM October 2026 (UNEP-WCMC, Protected Planet) and World Database of KBAs September 2026. Areas are measured in the Mollweide equal-area projection.

| Country | Land, PAs + OECMs | Sea | Folder |
|---|---|---|---|
| Tunisia | 7.93% | 1.07% | `tunisia/` |
| Algeria | 54.32% | 0.07% | `algeria/` |
| Morocco (Western Sahara excluded, as in Protected Planet) | 33.70% | 0.33% | `morocco/` |
| Morocco including Western Sahara | 20.42% | 0.16% | `morocco_incl_western_sahara/` |
| Libya | 0.13% | 0.63% | `libya/` |
| Egypt (Halaib Triangle excluded) | 11.24% | 3.62% | `egypt/` |

## Contents
- `GBF_Indicator_3.1_National_Tool.xlsx`: the blank calculation tool.
- `<country>/03_analysis/scripts/`: the Python pipeline, driven by `country.json`:
  1. `00_prepare_layers.py`: clip the global layers.
  2. `01_gis_flatten.py`: flatten the PAs and OECMs.
  3. `02_kba_overlay.py`: KBA coverage.
  4. `03_wetlands_glwd.py`: wetlands.
  5. `04_make_config.py` and `05_build_tool.py`: fill the workbook.
  6. `06_make_guide.py`: build the guide.
- `<country>/03_analysis/outputs/`: results tables (CSV, JSON).
- `<country>/04_tool/`: the filled Excel workbook for that country.
- `<country>/05_guide/`: an illustrated HTML walkthrough.
- `<country>/README.md`: results and method choices.
- `north_africa_dashboard/`: dashboard build scripts and the static sites:
  - `wwf_site/`: the WWF version, https://north-africa-30x30-wwf-theta.vercel.app
  - `wwf_site_ws/`: the WWF version with Morocco including Western Sahara, https://north-africa-30x30-wwf-ws.vercel.app
  - `vercel_site/`: the plain version.
- `Andorra_*`: the first, small worked example.

## Not included
The repository holds code, workbooks and outputs only. To re-run the analysis, download the inputs into each country's `01_data/` folder (paths in `country.json` and the country READMEs).

Spatial layers (shapefiles, GeoPackages, GeoJSON), raw input data and the reference documents (`02_documents/`) are left out. The inputs are:
- **WDPA / WD-OECM:** https://www.protectedplanet.net
- **Key Biodiversity Areas:** https://www.keybiodiversityareas.org (licensed: request through the KBA website or IBAT)
- **RESOLVE Ecoregions 2017:** https://ecoregions.appspot.com
- **Marine Ecoregions of the World:** https://www.marineregions.org
- **HydroRIVERS:** https://www.hydrosheds.org/products/hydrorivers
- **GLWD v2:** https://www.hydrosheds.org/products/glwd
- **GMBA Mountain Inventory v2:** https://www.earthenv.org/mountains
- **geoBoundaries:** https://www.geoboundaries.org
- **Marine Regions EEZ v12:** https://www.marineregions.org

## Data terms
- **KBA content:** the per-KBA coverage tables and the simplified KBA outlines in the dashboard data come from the World Database of Key Biodiversity Areas. They remain subject to its terms of use (© KBA Partnership; see keybiodiversityareas.org).
- **Protected-area data:** WDPA / WD-OECM content is subject to the UNEP-WCMC terms of use.
- **WWF assets:** the WWF logo and font in `wwf_site*/` belong to WWF.
