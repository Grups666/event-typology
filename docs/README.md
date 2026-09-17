# Global Catchment Atlas

Static GitHub Pages application, using the Tereon map foundation from
https://github.com/Grups666/tereon. Template revision and data checksums are
recorded in `modules/event-typology/provenance.json`.

The map displays polygon centroids, not catchment boundaries or metadata coordinates.
Coordinates are computed in the manuscript's regional Albers Equal Area projections
and transformed back to longitude/latitude, using `Gauged_Catchments_Boundaries.gpkg`.
Countries outside the six regional panels use the manuscript's global projection.
The palette is exported directly from `codebase/utils.py`.
Dormant-season data contain 4,838 catchments; growing-season data contain 4,797.
Missing seasonal records and coherence values are never replaced with zero.
Event types and coherence are read from the manuscript metadata without recalculation.
The type map reproduces the paper's concentric symbols. Inner circles show the
primary type; outer rings show the secondary type for compound classifications,
or gray when its stored percentage is below 25, matching the original plotter.
Single-type classifications use the same color for the center and outer ring.
Both types and the original composition are available in the inspector.
The only thematic map is hydro-meteorological type. Consistency and daily/weekly
coherence remain available in each catchment's inspector and CSV download.
Optional outline layers and the layer controls are not exposed in this atlas.
The optional high-consistency filter uses the strict CI > 0.9 criterion.
CSV downloads contain the currently filtered seasonal records.

The foundation provides the map, pan/zoom, layer manager, and inspector. The
event-typology module provides study locations, seasonal controls, styling,
filtering, and the two-season comparison. Its manifest can also be loaded into
Tereon directly using the published module.json URL.

## Rebuild

Run from the repository root with a local Tereon checkout and manuscript data:

```sh
python scripts/build_site.py --template /path/to/tereon --data /path/to/metadata-directory
```

The input directory must contain metadata_dormant.csv, metadata_growing.csv, and
Gauged_Catchments_Boundaries.gpkg. Rebuilding requires GeoPandas and Cartopy.
CSV longitude/latitude fields contain the displayed polygon centroids.
Only the fields listed in the build script are exported. All basemap assets are
served locally, so the default map requires no Mapbox token or remote map server.
Tereon retains its original basemap source attribution in the map footer.
