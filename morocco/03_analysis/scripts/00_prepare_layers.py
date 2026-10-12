"""Clip the global reference layers to the country in country.json.

Writes country clips of RESOLVE Ecoregions 2017, Marine Ecoregions of the World (VLIZ WFS),
HydroRIVERS v1.0 and the GMBA Mountain Inventory v2.0 into ../../01_data.
GLWD v2 is read directly from its global zip by 03_wetlands_glwd.py.
"""
import json, os, zipfile, urllib.request
import geopandas as gpd
from shapely.geometry import box
from shapely.ops import unary_union
from shapely.validation import make_valid


def polys(g):
    """Valid, polygon-only geometry (inputs such as some EEZ polygons are invalid; clips can leave line slivers)."""
    g = make_valid(g)
    if g.geom_type in ("Polygon", "MultiPolygon"):
        return g
    return unary_union([p for p in getattr(g, "geoms", []) if p.geom_type in ("Polygon", "MultiPolygon")])


def clean(gdf):
    gdf = gdf.copy()
    gdf["geometry"] = gdf.geometry.apply(polys)
    return gdf[~gdf.geometry.is_empty]

HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(f"{HERE}/country.json"))
ISO = C["iso3"]
DATA = f"{HERE}/../../01_data"
G = {k: os.path.normpath(os.path.join(HERE, v)) for k, v in C["global_sources"].items()}

land = clean(gpd.read_file(f"{DATA}/boundaries/geoBoundaries-{ISO}-ADM0.geojson"))
eez = clean(gpd.read_file(f"{DATA}/boundaries/MarineRegions_EEZ_v12_{ISO}.geojson"))
for g, n in ((land, "geoBoundaries"), (eez, "MarineRegions_EEZ_v12")):
    g.to_file(f"{DATA}/boundaries/{n}-{ISO}.shp" if n == "geoBoundaries" else f"{DATA}/boundaries/{n}_{ISO}.shp")
L = land.union_all()
minx, miny, maxx, maxy = L.bounds
bb = (minx - 0.5, miny - 0.5, maxx + 0.5, maxy + 0.5)


def shp_in_zip(z, stem):
    return next(n for n in zipfile.ZipFile(z).namelist() if n.endswith(".shp") and stem in n and "__MACOSX" not in n)


# terrestrial ecoregions
eco = gpd.read_file(f"/vsizip/{G['ecoregions_zip']}/{shp_in_zip(G['ecoregions_zip'], 'Ecoregions2017')}", bbox=bb)
eco = clean(gpd.clip(clean(eco[eco.intersects(L)]), land))
eco.to_file(f"{DATA}/ecoregions/RESOLVE_Ecoregions2017_{ISO}_clip.shp")
print("ecoregions:", sorted(set(eco.ECO_NAME)))

# marine ecoregions (MEOW) intersecting the EEZ
ex = eez.total_bounds
url = ("https://geo.vliz.be/geoserver/Ecoregions/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=Ecoregions:ecoregions"
       f"&bbox={ex[0]-1},{ex[1]-1},{ex[2]+1},{ex[3]+1}&outputFormat=application/json")
urllib.request.urlretrieve(url, f"{DATA}/marine_ecoregions/MEOW_bbox.geojson")
print("MEOW:", list(gpd.read_file(f"{DATA}/marine_ecoregions/MEOW_bbox.geojson").ecoregion))

# rivers
riv = gpd.read_file(f"/vsizip/{G['hydrorivers_zip']}/{shp_in_zip(G['hydrorivers_zip'], 'HydroRIVERS')}", bbox=tuple(L.bounds))
riv = gpd.clip(riv, land).explode(index_parts=False)
riv = riv[riv.geometry.geom_type.isin(["LineString", "MultiLineString"])]     # drop point slivers from the clip
riv.to_file(f"{DATA}/inland_waters/HydroRIVERS_v10_{ISO}_clip.shp")
print("river reaches:", len(riv))

# mountains
gm = gpd.read_file(f"/vsizip/{G['gmba_zip']}/{shp_in_zip(G['gmba_zip'], 'GMBA_Inventory')}", bbox=bb)
gm = clean(gpd.clip(clean(gm[gm.intersects(L)]), land))
gm.to_file(f"{DATA}/mountains/GMBA_Inventory_v2.0_{ISO}_clip.shp")
print("mountain ranges:", len(gm))
