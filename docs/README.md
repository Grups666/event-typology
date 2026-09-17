# Global Catchment Atlas

Static GitHub Pages application, using the Tereon map foundation from
https://github.com/Grups666/tereon. Template revision and data checksums are
recorded in `modules/event-typology/provenance.json`.

The map displays catchment representative locations, not catchment boundaries.
Dormant-season data contain 4,838 catchments; growing-season data contain 4,797.
Missing seasonal records and coherence values are never replaced with zero.
Event types and coherence are read from the manuscript metadata without recalculation.
The type map shows the primary event type; both primary and secondary types and
the original percentage composition are available in the catchment inspector.
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

The input directory must contain metadata_dormant.csv and metadata_growing.csv.
Only the fields listed in the build script are exported. All basemap assets are
served locally, so the default map requires no Mapbox token or remote map server.
Tereon retains its original basemap source attribution in the map footer.
