# North Africa 30×30 – WWF graphic-chart version

Static site styled to the WWF graphic chart (HWC Conference/RQ5/Graphic Chart WWF):
- Colour: black and white as the principal palette, with the WWF secondary palette assigned by category (at the user's request, beyond the guideline's two-colour suggestion):
  protected areas Green, OECMs Orange, sea Blue, wetlands/freshwater Aqua, KBAs Berry, KBA classes Green / Medium Green / Yellow / Red,
  governance Green / Orange / Berry / Brown, effectiveness Green / Orange, countries Tunisia Red, Algeria Brown, Morocco Berry, Libya Olive, Egypt Aqua.
- Type: WWF font (upper case) for headlines, tabs and key figures; Georgia for narrative text; Open Sans for captions, charts and tables (fonts in /fonts).
- Maps: WWF map style – dark grey neighbours, light grey country of interest, white/blue-tint sea.
- WWF Box Logo top right of the black title box; ownership line in the footer.

Same data, pages and code as ../vercel_site (shared app.js logic, only colour and type tokens differ; KBA class colours adjusted).
Open locally with any static server, e.g. `python3 -m http.server` in this folder, then http://localhost:8000.
Not published anywhere: it carries WWF's name, logo and font, so publish only with WWF's approval.

## Clickable country map

On the Country tab, hovering any protected area, OECM or KBA shows its name. Clicking it opens a card that lists every feature under the pointer, overlaps included. The site that holds the area (the one with the largest net area) is listed first. The card shows designation, year, IUCN category, governance, the net land and sea area counted, and the last evaluation; for a KBA it shows coverage, class and groups.

Site shapes come from `data/sitesgeo.json`, built by `../build_site_shapes.py`, which reads each country's `PA_OECM_included_buffered_moll.gpkg`. They are joined to `data/sites.json` by `site_id`. Re-run the script whenever the country analyses change.
