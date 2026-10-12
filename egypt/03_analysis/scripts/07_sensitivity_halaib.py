"""Sensitivity check: Egypt's Indicator 3.1 with the Halaib Triangle (land and overlapping-claim waters) included.

Uses the same sites and rules as 01_gis_flatten.py; only the base map changes. Writes ../outputs/sensitivity_halaib.json.
"""
import json, os
import geopandas as gpd, pandas as pd
from shapely.ops import unary_union
from shapely.validation import make_valid

HERE = os.path.dirname(os.path.abspath(__file__))
DATA, OUT = f"{HERE}/../../01_data", f"{HERE}/../outputs"
M, KM2 = "ESRI:54009", 1e6


def polys(g):
    g = make_valid(g)
    if g.geom_type in ("Polygon", "MultiPolygon"):
        return g
    return unary_union([p for p in getattr(g, "geoms", []) if p.geom_type in ("Polygon", "MultiPolygon")])


land = polys(gpd.read_file(f"{DATA}/boundaries/geoBoundaries-EGY-ADM0_incl_Halaib.geojson").to_crs(M).geometry.apply(make_valid).union_all())
ov = gpd.read_file(f"{DATA}/boundaries/MarineRegions_overlapping_claims_EGY.geojson")
eez = pd.concat([gpd.read_file(f"{DATA}/boundaries/MarineRegions_EEZ_v12_EGY.geojson"), ov[ov.geoname.str.contains("Halaib")]])
sea = polys(polys(eez.to_crs(M).geometry.apply(make_valid).union_all()).difference(land))
sites = gpd.read_file(f"{OUT}/PA_OECM_included_buffered_moll.gpkg").to_crs(M)
pa = polys(unary_union(list(sites.geometry.apply(make_valid))))
res = dict(land_km2=land.area / KM2, sea_km2=sea.area / KM2, pa_land_km2=pa.intersection(land).area / KM2, pa_sea_km2=pa.intersection(sea).area / KM2)
res["land_pct"] = res["pa_land_km2"] / res["land_km2"] * 100
res["sea_pct"] = res["pa_sea_km2"] / res["sea_km2"] * 100
json.dump(res, open(f"{OUT}/sensitivity_halaib.json", "w"), indent=1)
print(json.dumps(res, indent=1))
