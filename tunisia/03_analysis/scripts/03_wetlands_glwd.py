"""Inland waters – lakes and wetlands covered by protected areas, from GLWD v2.0 (Lehner et al. 2025).

GLWD v2 gives, for each 15 arc-second cell, the absolute area (ha x10) of each of 33 wetland classes.
Coverage = sum over cells of (class area x fraction of the cell inside the flattened PA layer).
The cell fraction is computed by rasterising the flat layer on a 10 x 10 sub-grid of every cell.
Run after 01_gis_flatten.py.
"""
import json, os, zipfile
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.windows import from_bounds
from rasterio.features import rasterize
from rasterio.transform import Affine

HERE = os.path.dirname(os.path.abspath(__file__))
DATA, OUT = f"{HERE}/../../01_data", f"{HERE}/../outputs"
ZIP = f"{DATA}/inland_waters/_global_download/GLWD_v2_0_area_by_class_ha_tif.zip"
CLIP = f"{DATA}/inland_waters/GLWD_v2_TUN"
os.makedirs(CLIP, exist_ok=True)
SUB = 10

CLASSES = {1: "Freshwater lake", 2: "Saline lake", 3: "Reservoir", 4: "Large river", 5: "Large estuarine river",
           6: "Other permanent waterbody", 7: "Small streams", 8: "Lacustrine, forested", 9: "Lacustrine, non-forested",
           10: "Riverine, regularly flooded, forested", 11: "Riverine, regularly flooded, non-forested",
           12: "Riverine, seasonally flooded, forested", 13: "Riverine, seasonally flooded, non-forested",
           14: "Riverine, seasonally saturated, forested", 15: "Riverine, seasonally saturated, non-forested",
           16: "Palustrine, regularly flooded, forested", 17: "Palustrine, regularly flooded, non-forested",
           18: "Palustrine, seasonally saturated, forested", 19: "Palustrine, seasonally saturated, non-forested",
           20: "Ephemeral, forested", 21: "Ephemeral, non-forested", 22: "Arctic/boreal peatland, forested",
           23: "Arctic/boreal peatland, non-forested", 24: "Temperate peatland, forested", 25: "Temperate peatland, non-forested",
           26: "Tropical/subtropical peatland, forested", 27: "Tropical/subtropical peatland, non-forested", 28: "Mangrove",
           29: "Saltmarsh", 30: "Large river delta", 31: "Other coastal wetland", 32: "Salt pan, saline/brackish wetland",
           33: "Rice paddies"}
GROUP = {**{c: "Lakes and reservoirs" for c in (1, 2, 3, 6)}, **{c: "River channels (counted as river length)" for c in (4, 5, 7)},
         **{c: "Lacustrine wetlands" for c in (8, 9)}, **{c: "Riverine wetlands" for c in range(10, 16)},
         **{c: "Palustrine wetlands" for c in range(16, 20)}, **{c: "Ephemeral wetlands" for c in (20, 21)},
         **{c: "Peatlands" for c in range(22, 28)}, **{c: "Coastal wetlands" for c in (28, 29, 30, 31)},
         32: "Salt pans and saline wetlands", 33: "Rice paddies (anthropogenic, excluded)"}
EXCLUDE = {4, 5, 7, 33}     # river channels are the 'rivers' row; rice paddies are anthropogenic

realms = gpd.read_file(f"{OUT}/base_map_realms_TUN.shp").set_index("realm")   # EPSG:4326
LAND = realms.loc["terrestrial", "geometry"]
flat = gpd.read_file(f"{OUT}/PA_flattened_TUN_wgs84.geojson").set_index("realm")
PA_T = flat.loc["terrestrial", "geometry"]
minx, miny, maxx, maxy = LAND.bounds

zf = zipfile.ZipFile(ZIP)
import re
tifs = {int(m.group(1)): n for n in zf.namelist() if (m := re.search(r"_class_(\d\d)_ha_x10\.tif$", n))}
first = True
rows = []
for c in sorted(k for k in tifs if k != 0):
    with rasterio.open(f"/vsizip/{ZIP}/{tifs[c]}") as src:
        win = from_bounds(minx - 0.01, miny - 0.01, maxx + 0.01, maxy + 0.01, src.transform).round_offsets().round_lengths()
        arr = src.read(1, window=win).astype("float64")
        nod = src.nodata
        tr = src.window_transform(win)
        prof = src.profile.copy()
    if nod is not None:
        arr[arr == nod] = 0
    ha = arr / 10.0
    if first:   # fraction of each cell inside the land realm and inside the PA layer (10x10 sub-grid)
        H, W = arr.shape
        sub_tr = tr * Affine.scale(1 / SUB)
        def frac(geom):
            m = rasterize([(geom, 1)], out_shape=(H * SUB, W * SUB), transform=sub_tr, fill=0, dtype="uint8", all_touched=False)
            return m.reshape(H, SUB, W, SUB).mean(axis=(1, 3))
        F_LAND = frac(LAND)
        F_PA = frac(PA_T.intersection(LAND))
        first = False
    tot, cov = (ha * F_LAND).sum() / 100, (ha * F_PA).sum() / 100      # km2
    rows.append(dict(class_id=c, class_name=CLASSES[c], group=GROUP[c], counted="N" if c in EXCLUDE else "Y",
                     extent_km2=tot, pa_km2=cov, pa_pct=cov / tot * 100 if tot else None))
    if tot > 0:
        prof.update(height=arr.shape[0], width=arr.shape[1], transform=tr, compress="deflate")
        with rasterio.open(f"{CLIP}/GLWD_v2_0_class_{c:02d}_ha_x10_TUN.tif", "w", **prof) as dst:
            dst.write(arr.astype(prof["dtype"]), 1)

df = pd.DataFrame(rows)
df.to_csv(f"{OUT}/glwd_wetland_coverage_by_class.csv", index=False)
g = df[df.extent_km2 > 0].groupby(["group", "counted"], as_index=False)[["extent_km2", "pa_km2"]].sum()
g["pa_pct"] = g.pa_km2 / g.extent_km2 * 100
g.sort_values("extent_km2", ascending=False).to_csv(f"{OUT}/glwd_wetland_coverage_by_group.csv", index=False)
cnt = df[df.counted == "Y"]
res = dict(lakes_wetlands_km2=cnt.extent_km2.sum(), lakes_wetlands_pa_km2=cnt.pa_km2.sum(),
           pct=cnt.pa_km2.sum() / cnt.extent_km2.sum() * 100,
           river_channels_km2=df[df.class_id.isin([4, 5, 7])].extent_km2.sum(),
           river_channels_pa_km2=df[df.class_id.isin([4, 5, 7])].pa_km2.sum())
json.dump(res, open(f"{OUT}/glwd_results.json", "w"), indent=1)
print(json.dumps(res, indent=1))
print(g.round(1).sort_values("extent_km2", ascending=False).to_string(index=False))
print(df[df.extent_km2 > 0.5].round(1).sort_values("extent_km2", ascending=False).to_string(index=False))
