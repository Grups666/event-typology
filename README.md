# Figures Generation Module

This module provides a modular and configurable approach to generating all figures for the paper. The code has been refactored from the original notebook into a clean, reusable structure.

## Structure

```
figures_generation/
├── codebase/
│   ├── __init__.py          # Main module exports
│   ├── config.py            # Configuration classes (FigureConfig, RegionConfig)
│   ├── data_loader.py       # Data loading utilities
│   ├── figure_generators.py # High-level figure generation functions
│   ├── plotters.py          # All plotting functions
│   └── utils.py             # Utility functions (colors, helpers)
├── figures/                 # Generated static figures
│   ├── Fig. 1/              # Regional catchment type maps (dormant season)
│   ├── Fig. 2/              # Seasonal transition analysis
│   ├── Fig. 3/              # Coherence-consistency heatmap (dormant)
│   ├── Fig. 4/              # Magnitude CV vs coherency (dormant)
│   ├── Fig. 5/              # Hydrologic response comparison
│   ├── Fig. S1/             # SSI CDF
│   ├── Fig. S2/             # Global catchment type maps
│   ├── Fig. S3/             # Regional catchment type maps (growing season)
│   ├── Fig. S4/             # Consistency boxplot
│   ├── Fig. S5/             # Coherence-consistency heatmap (growing)
│   ├── Fig. S6/             # Magnitude CV vs coherency (growing)
│   └── Fig. S7/             # Hydrologic response comparison (growing)
├── interactive_maps/        # Interactive visualizations
│   └── Global_Interactive_Map.html  # Global interactive catchment type map
└── notebooks/
    └── generate_figures.ipynb  # Simplified notebook for generating figures
```

## Features

1. **Modular Design**: All plotting functions are organized in separate modules
2. **Configuration-Based**: Important parameters are centralized in `FigureConfig`
3. **Simple Interface**: The `generate_figures.ipynb` notebook provides the simplest interface
4. **Region Support**: Easy specification of regions with automatic extent and country code handling
5. **Interactive Maps**: Global interactive catchment type visualization using Kepler.gl

## Usage

### Basic Usage

Open `notebooks/generate_figures.ipynb` and run the cells:

```python
from codebase import generate_figure_1, FigureConfig

# Initialize configuration
config = FigureConfig()

# Generate a global map
generate_figure_1(
    region=None,  # Global map
    season='dormant',
    save=True,
    show=False,
    config=config
)
```

### Regional Maps

For regional maps, simply specify the region name:

```python
# Display one region without saving (only main map shown)
generate_figure_1(
    region='north_america',
    season='dormant',
    save=False,
    show=True,
    config=config
)

# Generate all regions (saves without showing)
generate_figure_1(
    region=None,  # Generates for all regions
    season='dormant',
    save=True,
    show=False,
    config=config
)
```

Available regions:
- `'oceania'`
- `'southern_africa'`
- `'europe'`
- `'north_america'`
- `'south_america'`
- `'southeast_asia'`
- `None` (global)

### Interactive Maps

A global interactive catchment type map is available in `interactive_maps/Global_Interactive_Map.html`. Open this file in a web browser to explore the global distribution of catchment types interactively.

## Data Structure

This module expects data organized in the following structure (based on `Event_Typology`):

```
Event_Typology/
├── Gauged_Catchments_Boundaries.gpkg  # GeoPackage with catchment boundaries
│   └── Layer: Gauged_Catchments_Boundaries
│       └── Index: GCIN (Gauged Catchment Identification Number)
├── metadata_dormant.csv               # Metadata for dormant season
│   └── Columns: GCIN, country, longitude, latitude, snow_fraction,
│                KGE_calibration, KGE_evaluation, primary_event_type,
│                secondary_event_type, event_type_with_percentiles,
│                consistency_index, WI-Q_weekly, WI-Q_daily
├── metadata_growing.csv                # Metadata for growing season
│   └── Same structure as metadata_dormant.csv
├── events_dormant.csv                  # Event-level data for dormant season
│   └── Columns: Event ID, GCIN, start_precip_date, end_precip_date,
│                duration_precip, start_stormflow_date, end_stormflow_date,
│                duration_stormflow, volume_precip_mm, volume_stormflow_mm,
│                runoff_ratio, soil_saturation_index, streamflow_mm,
│                event_magnitude_response_index, snowpack_mm,
│                snowmelt_contribution_ratio, event_type
├── events_growing.csv                  # Event-level data for growing season
│   └── Same structure as events_dormant.csv
├── growing_months_by_GCIN.pkl          # Dictionary mapping GCIN to growing months
│   └── Format: {GCIN: [list of month numbers]}
└── daily_data/
    ├── observations/                   # Daily observation data
    │   └── {GCIN}.csv                  # One CSV file per catchment
    │       └── Columns: date (index), and various daily variables
    └── simulations/                    # Daily simulation data (optional)
        └── {GCIN}.csv                  # One CSV file per catchment
```

### Key Data Fields

- **GCIN**: Unique identifier for each gauged catchment
- **event_type**: Classification of events (e.g., 'Rain-Dry', 'Snow-Wet', 'ROS-Mod')
- **event_type_with_percentiles**: Event type with percentage composition
- **consistency_index**: Measure of consistency in event type classification
- **WI-Q_weekly/daily**: Weekly and daily coherency indices
- **soil_saturation_index**: Soil moisture saturation level
- **event_magnitude_response_index**: Magnitude of hydrologic response

## Figure Organization

### Main Figures

- **Figure 1**: Regional catchment type maps (dormant season)
  - Save path: `figures/Fig. 1/{region_name}/`
  - Includes: Spatial distribution, longitudinal/latitudinal distributions, type composition

- **Figure 2**: Seasonal transition analysis
  - Save path: `figures/Fig. 2/{region_name}_Seasonal_Transition.png`

- **Figure 3**: Coherence-consistency heatmap (dormant season)
  - Save path: `figures/Fig. 3/Heatmap_Coherence_Consistency_dormant.png`

- **Figure 4**: Magnitude CV vs coherency (dormant season)
  - Save path: `figures/Fig. 4/Mag_CV_Vs_Coherency_dormant.png`

- **Figure 5**: Hydrologic response comparison
  - Save path: `figures/Fig. 5/Mag_Comparison_Combined_CDF.png`

### Supplementary Figures

- **Figure S1**: Soil Saturation Index CDF
  - Save path: `figures/Fig. S1/SSI_CDF.png`

- **Figure S2**: Global catchment type maps
  - Save path: `figures/Fig. S2/Spatial_Distribution_{season}.png`

- **Figure S3**: Regional catchment type maps (growing season)
  - Save path: `figures/Fig. S3/{region_name}/`
  - Same structure as Figure 1

- **Figure S4**: Consistency boxplot
  - Save path: `figures/Fig. S4/Consistency_Boxplot_{season}.png`

- **Figure S5**: Coherence-consistency heatmap (growing season)
  - Save path: `figures/Fig. S5/Heatmap_Coherence_Consistency_growing.png`

- **Figure S6**: Magnitude CV vs coherency (growing season)
  - Save path: `figures/Fig. S6/Mag_CV_Vs_Coherency_growing.png`

- **Figure S7**: Hydrologic response comparison (growing season)
  - Save path: `figures/Fig. S7/Mag_Comparison_Combined_CDF.png`

## Configuration Parameters

Key parameters in `FigureConfig`:

- **Colors**: Category colors, season colors
- **Map Settings**: Figure size, DPI, point size, line width
- **Display Settings**: Show DPI (for display), save DPI (for saving)
- **Figure-Specific**: Settings for each figure type
- **Save Paths**: Base path for saving figures
- **Default Regions**: List of regions for batch processing

## Available Functions

### High-Level Generators (in `figure_generators.py`)

- `generate_figure_1()`: Regional catchment type maps
- `generate_figure_2()`: Seasonal transition analysis
- `generate_figure_s1()`: SSI CDF
- `generate_figure_s3()`: Regional maps (growing season)
- `generate_all_figures()`: Generate all figures in batch

### Plotting Functions (in `plotters.py`)

- `plot_ssi_cdf()`: Figure S1 - Soil Saturation Index CDF
- `plot_catchment_type_maps()`: Figure 1/S2/S3 - Catchment type maps
- `plot_seasonal_transition()`: Figure 2 - Seasonal transition analysis
- `plot_coherence_consistency_heatmap()`: Figure 3/S5 - Heatmaps
- `plot_magnitude_cv_vs_coherency()`: Figure 4/S6 - CV vs coherency
- `plot_hydrologic_response_comparison()`: Figure 5/S7 - Response comparison
- `plot_distribution_by_axis()`: Distribution plots (helper)
- `plot_type_change_pie()`: Pie chart (helper)
- `plot_catchments_map()`: Base map plotting function

### Data Loading (in `data_loader.py`)

- `DataLoader`: Centralized data loading class
- `get_data_loader()`: Get or create global data loader instance

## Notes

1. All functions support the `config` parameter for centralized configuration
2. Regional maps automatically adjust extent and country codes based on region name
3. When `show=True`, only the main map is displayed (panels are skipped)
4. When `save=True`, both the main map and all panels are saved
5. File names follow academic conventions with underscores and capitalized words (e.g., `Spatial_Distribution.png`)
6. The `DataLoader` class uses lazy loading to optimize memory usage
7. Interactive maps are standalone HTML files that can be opened directly in a web browser

## Migration from Original Notebook

The original plotting code has been:
1. Extracted into modular functions in `plotters.py`
2. Parameterized via `FigureConfig`
3. Organized into high-level generators in `figure_generators.py`
4. Simplified in `generate_figures.ipynb` with easy-to-use interfaces

The functionality remains the same, but the code is now:
- More maintainable
- Easier to customize
- Better organized
- Reusable across projects
