"""Reproduce the manuscript's region-specific projected catchment centroids."""
import hashlib
import math
import runpy

import cartopy.crs as ccrs
import geopandas as gpd


def paper_symbols(root, data, ids):
    regions = runpy.run_path(str(root / 'codebase/config.py'))['DEFAULT_REGIONS']
    colors = runpy.run_path(str(root / 'codebase/utils.py'))['get_category_colors']()
    source = data / 'Gauged_Catchments_Boundaries.gpkg'
    gdf = gpd.read_file(source, layer='Gauged_Catchments_Boundaries').set_index('GCIN')
    gdf = gdf[gdf.index.notna()].copy()
    gdf.index = gdf.index.astype(int)
    assert gdf.index.is_unique
    gdf = gdf.loc[gdf.index.intersection(ids)]
    assert set(gdf.index) == set(ids), 'Missing catchment boundaries'
    assert not gdf.geometry.is_empty.any() and not gdf.geometry.isna().any()
    coordinates = {}
    groups = {}

    def project(frame, region):
        if frame.empty:
            return
        b = frame.total_bounds
        projection = ccrs.AlbersEqualArea(
            central_longitude=(b[0] + b[2]) / 2,
            central_latitude=(b[1] + b[3]) / 2,
        )
        centers = frame.to_crs(projection.proj4_init).geometry.centroid.to_crs(gdf.crs)
        for gcin, point in centers.items():
            assert math.isfinite(point.x) and math.isfinite(point.y)
            assert -180 <= point.x <= 180 and -90 <= point.y <= 90
            coordinates[int(gcin)] = (point.x, point.y)
        groups[region] = {'catchments': len(frame), 'projection': projection.proj4_init}

    for name, region in regions.items():
        if name != 'globe':
            frame = gdf[gdf.country.isin(region.countries)]
            assert not set(frame.index).intersection(coordinates), 'Overlapping paper regions'
            project(frame, name)
    # Countries outside the six panels use the paper's global-map projection.
    missing = set(ids) - set(coordinates)
    if missing:
        regional = coordinates.copy()
        project(gdf, 'globe')
        coordinates.update(regional)
        groups['globe']['used_for_catchments'] = len(missing)
    assert set(coordinates) == set(ids)
    provenance = {'file': source.name, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                  'method': 'AlbersEqualArea polygon centroid; projection centered on each manuscript region bounding box',
                  'regions': groups}
    return coordinates, colors, provenance
