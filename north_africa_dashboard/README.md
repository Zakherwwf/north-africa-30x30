# North Africa 30×30 dashboard

Live dashboard: https://claude.ai/artifact/TLG2EikbxKYUEjBi3N3V1F

Pages: Overview (regional figures, choropleth map, coverage bars, country table, regional narrative) · Country (country picker, headline figures,
zoomable map with PA / OECM / KBA / sea layers, coverage over time, ecoregions, wetlands, governance and effectiveness, searchable KBA and site tables,
country report) · Compare (time series, KBA groups, inland waters, Protected Planet cross-check, data quality, least-covered ecoregions) · Report.

Rebuild:
1. `python build_dashboard_data.py` – reads ../<country>/03_analysis/outputs for Tunisia, Algeria, Morocco, Libya, Egypt and writes data/*.json
2. `python build_narratives.py` – writes data/narratives.json from the same figures
3. Upload data/*.json to the dashboard as attached files and update the dataset documents; page/index.html and page/app.js are the page files.
