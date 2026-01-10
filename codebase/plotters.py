"""
Plotting functions for figure generation.
All plotting functions are modularized and optimized from the original notebook.
"""

import os
import math
import warnings
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from typing import Dict, List, Optional, Tuple, Union
from scipy.interpolate import interp1d
from scipy import stats
from matplotlib.gridspec import GridSpec

from .config import FigureConfig, RegionConfig, DEFAULT_REGIONS
from .utils import get_category_colors, get_season_colors


def plot_catchments_map(
    gdf: gpd.GeoDataFrame,
    values: Optional[pd.Series] = None,
    figsize: Tuple[float, float] = (20, 12),
    dpi: int = 300,
    extent: Optional[List[float]] = None,
    ocean_color: str = '#e6f2ff',
    land_color: str = 'whitesmoke',
    border_color: str = 'black',
    coastline_color: str = 'black',
    lake_alpha: float = 0.3,
    river_alpha: float = 0.3,
    catchment_edgecolor: str = 'indianred',
    catchment_facecolor: str = 'mistyrose',
    catchment_linewidth: float = 0.3,
    show_as_points: bool = False,
    point_size: float = 20,
    linewidth: float = 1.2,
    point_alpha: float = 1,
    cmap: Optional[str] = None,
    title: Optional[str] = None,
    save: bool = False,
    save_path: Optional[str] = None,
    show: bool = True,
    return_extent: bool = False,
    category_colors: Optional[Dict[str, str]] = None,
    country_codes: Optional[List[str]] = None,
    ignore_types: Optional[List[str]] = None,
    legend_loc: Optional[str] = 'lower left',
    auto_adjust_figsize: bool = False,
    config: Optional[FigureConfig] = None,
) -> Optional[Dict]:
    """
    Plot catchment map with automatic distinction between continuous and categorical data.
    
    This is the main map plotting function, optimized and modularized from the original notebook.
    
    Parameters:
    -----------
    auto_adjust_figsize : bool, default=False
        If True, automatically adjust figsize based on extent aspect ratio.
        If False, use the provided figsize parameter.
    """
    if config is None:
        config = FigureConfig()
    
    if category_colors is None:
        category_colors = config.category_colors
    if ignore_types is None:
        ignore_types = config.fig1_ignore_types
    if extent is None and country_codes:
        for region in DEFAULT_REGIONS.values():
            if set(country_codes).issubset(set(region.countries)) or region.countries == ['all']:
                extent = region.range
                break
    
    if extent and auto_adjust_figsize:
        lon_diff = abs(extent[0] - extent[1])
        lat_diff = abs(extent[2] - extent[3])
        point_size /= (lat_diff / 40)
        linewidth /= (lat_diff / 40)
        fig_x = lon_diff / lat_diff * point_size
        figsize = (fig_x, 12)
    
    display_dpi = config.show_dpi if show else config.save_dpi
    
    plt.figure(figsize=figsize, dpi=display_dpi)
    ax = plt.axes(projection=ccrs.PlateCarree())
    
    if country_codes is not None:
        possible_country_fields = ['country', 'COUNTRY', 'country_code', 'COUNTRY_CODE', 'iso_a2', 'ISO_A2']
        country_field = None
        for field in possible_country_fields:
            if field in gdf.columns:
                country_field = field
                break
        if country_field is not None:
            gdf = gdf[gdf[country_field].isin(country_codes)]
    
    if extent is not None:
        ax.set_extent(extent, crs=ccrs.PlateCarree())
    
    ax.set_facecolor(ocean_color)
    ax.add_feature(cfeature.LAND, facecolor=land_color)
    ax.add_feature(cfeature.BORDERS, linewidth=0.5, edgecolor=border_color)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5, edgecolor=coastline_color)
    ax.add_feature(cfeature.LAKES, alpha=lake_alpha)
    ax.add_feature(cfeature.RIVERS, alpha=river_alpha)
    
    if ignore_types is None:
        ignore_types = []
    elif isinstance(ignore_types, str):
        ignore_types = [ignore_types]
    
    is_categorical = False
    if values is not None:
        common_idx = gdf.index.intersection(values.index)
        gdf = gdf.loc[common_idx]
        values = values.loc[common_idx]
        gdf['__plot_values__'] = values
        
        vals = pd.Series(values)
        if (vals.dtype == object) or (vals.dtype.name == 'category') or (np.issubdtype(vals.dtype, np.integer) and vals.nunique() <= 10):
            is_categorical = True
        elif np.issubdtype(vals.dtype, np.floating) or np.issubdtype(vals.dtype, np.integer):
            is_categorical = False if vals.nunique() > 10 else True
        else:
            is_categorical = True
        
        if cmap is None:
            auto_cmap = 'tab20' if is_categorical else 'turbo'
        else:
            auto_cmap = cmap
        
        if show_as_points:
            points_gdf = gdf.copy()
            bounds = points_gdf.total_bounds
            center_lon = (bounds[0] + bounds[2]) / 2
            center_lat = (bounds[1] + bounds[3]) / 2
            
            proj = ccrs.AlbersEqualArea(central_longitude=center_lon, central_latitude=center_lat)
            points_gdf['geometry'] = (
                points_gdf.to_crs(proj.proj4_init)
                .geometry.centroid
                .to_crs(points_gdf.crs)
            )
            
            if is_categorical and category_colors is not None:
                point_data = []
                
                inner_radius = np.sqrt(point_size / np.pi)
                outer_radius = inner_radius + linewidth/1.815
                outer_size = np.pi * outer_radius**2
                
                for idx, row in points_gdf.iterrows():
                    value = str(row['__plot_values__'])
                    x, y = row['geometry'].x, row['geometry'].y
                    
                    if isinstance(idx, (int, np.integer)):
                        zorder = 10 + int(idx) % 1000
                    else:
                        zorder = 10 + abs(hash(str(idx))) % 1000
                    
                    def should_ignore_type(cat):
                        return any(cat == ignore_type or cat.startswith(ignore_type + '-') for ignore_type in ignore_types)
                    
                    if ' & ' not in value and ':' in value:
                        parts = value.split(':')
                        primary_type = parts[0]
                        
                        if should_ignore_type(primary_type):
                            continue
                        
                        point_data.append({
                            'x': x, 'y': y,
                            'inner_color': category_colors.get(primary_type, '#cccccc'),
                            'outer_color': category_colors.get(primary_type, '#cccccc'),
                            'inner_size': point_size,
                            'outer_size': outer_size,
                            'alpha': point_alpha,
                            'linewidth': linewidth,
                            'zorder': zorder
                        })
                    else:
                        try:
                            parts = value.split(' & ')
                            primary_part = parts[0].split(':')
                            secondary_part = parts[1].split(':')
                            
                            primary_type = primary_part[0]
                            primary_percent = float(primary_part[1]) if len(primary_part) > 1 else 0
                            secondary_type = secondary_part[0]
                            secondary_percent = float(secondary_part[1]) if len(secondary_part) > 1 else 0
                            
                            if should_ignore_type(primary_type):
                                continue
                            
                            if secondary_percent >= 25:
                                if secondary_type in category_colors:
                                    point_data.append({
                                        'x': x, 'y': y,
                                        'inner_color': category_colors.get(primary_type, '#cccccc'),
                                        'outer_color': category_colors.get(secondary_type, '#cccccc'),
                                        'inner_size': point_size,
                                        'outer_size': outer_size,
                                        'alpha': point_alpha,
                                        'linewidth': linewidth,
                                        'zorder': zorder
                                    })
                            else:
                                point_data.append({
                                    'x': x, 'y': y,
                                    'inner_color': category_colors.get(primary_type, '#cccccc'),
                                    'outer_color': '#666666',
                                    'inner_size': point_size,
                                    'outer_size': outer_size,
                                    'alpha': point_alpha,
                                    'linewidth': linewidth,
                                    'zorder': zorder
                                })
                        except (ValueError, IndexError):
                            pass
                
                point_data.sort(key=lambda p: p['zorder'])
                
                for point in point_data:
                    ax.scatter(point['x'], point['y'], c=point['inner_color'], s=point['inner_size'],
                              alpha=point['alpha'], edgecolor='none',
                              transform=ccrs.PlateCarree(), zorder=point['zorder'])
                    ax.scatter(point['x'], point['y'], c='none', s=point['outer_size'],
                              alpha=point['alpha'], edgecolor=point['outer_color'],
                              linewidth=point['linewidth'],
                              transform=ccrs.PlateCarree(), zorder=point['zorder'])
                
                if legend_loc is not None:
                    def should_ignore_type(cat):
                        return any(cat == ignore_type or cat.startswith(ignore_type + '-') for ignore_type in ignore_types)
                    
                    type_counts = {}
                    for val in gdf['__plot_values__'].dropna():
                        val_str = str(val)
                        if ' & ' in val_str:
                            types = val_str.split(' & ')
                            for t in types:
                                if ':' in t:
                                    t = t.split(':')[0]
                                type_counts[t] = type_counts.get(t, 0) + 1
                        else:
                            if ':' in val_str:
                                t = val_str.split(':')[0]
                            else:
                                t = val_str
                            type_counts[t] = type_counts.get(t, 0) + 1
                    
                    filtered_type_counts = {k: v for k, v in type_counts.items() if not should_ignore_type(k)}
                    sorted_types = sorted(filtered_type_counts.items(), key=lambda x: x[1], reverse=True)[:9]
                    displayed_types = {t[0] for t in sorted_types}
                    
                    handles = []
                    for cat in category_colors.keys():
                        if not should_ignore_type(cat) and cat in displayed_types:
                            handles.append(mpatches.Patch(color=category_colors[cat], label=f"{cat}"))
                    
                    ax.legend(handles=handles, loc=legend_loc, fontsize=20, title_fontsize=20, frameon=True)
            else:
                points_gdf.plot(ax=ax, column='__plot_values__', cmap=auto_cmap,
                               markersize=point_size, alpha=point_alpha, zorder=10,
                               transform=ccrs.PlateCarree())
        else:
            if is_categorical and category_colors is not None:
                def should_skip(value):
                    if pd.isna(value):
                        return False
                    val_str = str(value)
                    def should_ignore_type(cat):
                        return any(cat == ignore_type or cat.startswith(ignore_type + '-') for ignore_type in ignore_types)
                    
                    if ' & ' not in val_str and ':' in val_str:
                        primary_type = val_str.split(':')[0]
                        return should_ignore_type(primary_type)
                    elif ' & ' in val_str:
                        try:
                            parts = val_str.split(' & ')
                            primary_part = parts[0].split(':')
                            primary_type = primary_part[0]
                            return should_ignore_type(primary_type)
                        except:
                            return False
                    return False
                
                mask = ~gdf['__plot_values__'].apply(should_skip)
                gdf_filtered = gdf[mask].copy()
                
                color_map = gdf_filtered['__plot_values__'].map(category_colors)
                color_map = color_map.fillna('#cccccc')
                gdf_filtered.plot(ax=ax, color=color_map, linewidth=0, zorder=10,
                                 transform=ccrs.PlateCarree(), legend=False)
            else:
                gdf.plot(ax=ax, column='__plot_values__', cmap=auto_cmap, linewidth=0,
                        zorder=10, transform=ccrs.PlateCarree(), legend_kwds={'shrink': 0.5})
    else:
        if show_as_points:
            points_gdf = gdf.copy()
            bounds = points_gdf.total_bounds
            center_lon = (bounds[0] + bounds[2]) / 2
            center_lat = (bounds[1] + bounds[3]) / 2
            
            proj = ccrs.AlbersEqualArea(central_longitude=center_lon, central_latitude=center_lat)
            points_gdf['geometry'] = (
                points_gdf.to_crs(proj.proj4_init)
                .geometry.centroid
                .to_crs(points_gdf.crs)
            )
            
            points_gdf.plot(ax=ax, color=catchment_facecolor, markersize=point_size,
                           alpha=point_alpha, zorder=10, transform=ccrs.PlateCarree())
        else:
            gdf.plot(ax=ax, edgecolor=catchment_edgecolor, facecolor=catchment_facecolor,
                    linewidth=catchment_linewidth, zorder=10, transform=ccrs.PlateCarree())
    
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {'size': 20}
    gl.ylabel_style = {'size': 20}
    
    if title is None:
        if isinstance(values, pd.Series) and values.name:
            title = f"Catchments - {values.name}"
        else:
            title = "Catchments with Values" if values is not None else "Catchments Map"
    
    plot_extent = None
    if return_extent:
        x_min, x_max, y_min, y_max = ax.get_extent()
        plot_extent = {'x': (x_min, x_max), 'y': (y_min, y_max)}
    
    if save and save_path is not None:
        save_dir = os.path.dirname(save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
        plt.savefig(save_path, dpi=config.save_dpi, bbox_inches='tight')
    
    if show:
        plt.show()
    else:
        plt.close()
    
    return plot_extent


def plot_ssi_cdf(
    dormant_ssi: pd.Series,
    growing_ssi: pd.Series,
    all_ssi: pd.Series,
    dormant_color: str = '#AD1B26',
    growing_color: str = '#2E8B57',
    figsize: Tuple[float, float] = (4, 3),
    dpi: int = 600,
    quantiles: Tuple[float, float] = (1/3, 2/3),
    save_path: Optional[str] = None,
    show: bool = True,
    config: Optional[FigureConfig] = None,
) -> None:
    """
    Plot SSI cumulative distribution function (CDF).
    
    Figure S1: Soil Moisture State Classification
    
    Parameters:
    -----------
    show : bool, default=True
        If True, display the figure with show_dpi. If False, only save with save_dpi.
    """
    if config is None:
        config = FigureConfig()
    
    display_dpi = config.show_dpi if show else config.save_dpi
    plt.figure(figsize=figsize, dpi=display_dpi)
    
    all_ssi_sorted = np.sort(all_ssi)
    all_ssi_cdf = np.linspace(0, 1, len(all_ssi_sorted))
    
    plt.plot(all_ssi_sorted, all_ssi_cdf, label='Both Seasons', linewidth=1, color='black')
    plt.plot(np.sort(dormant_ssi), np.linspace(0, 1, len(dormant_ssi)),
             label='Dormant Season', linewidth=1, color=dormant_color)
    plt.plot(np.sort(growing_ssi), np.linspace(0, 1, len(growing_ssi)),
             label='Growing Season', linewidth=1, color=growing_color)
    
    ssi_33 = all_ssi.quantile(quantiles[0])
    ssi_66 = all_ssi.quantile(quantiles[1])
    
    plt.axvline(x=ssi_33, color='darkgray', linestyle='--', linewidth=2, alpha=0.8, zorder=5)
    plt.axvline(x=ssi_66, color='darkgray', linestyle='--', linewidth=2, alpha=0.8, zorder=5)
    
    # Interpolate to find y values
    interp_func = interp1d(all_ssi_sorted, all_ssi_cdf, kind='linear', bounds_error=False, fill_value=(0, 1))
    y_ssi_33 = interp_func(ssi_33)
    y_ssi_66 = interp_func(ssi_66)
    
    # Mark points
    plt.plot(ssi_33, y_ssi_33, 'ko', markersize=3, zorder=6, label='_nolegend_')
    plt.plot(ssi_66, y_ssi_66, 'ko', markersize=3, zorder=6, label='_nolegend_')
    
    # Add text annotations
    plt.text(ssi_33-0.01, 0.45, 'Dry-Mod Threshold', fontsize=7, ha='right', va='top', color='black', weight='bold')
    plt.text(ssi_33-0.01, 0.40, f'SSI = {ssi_33:.2f}', fontsize=7, ha='right', va='top', color='black')
    plt.text(ssi_66+0.01, 0.65, 'Mod-Wet Threshold', fontsize=7, ha='left', va='top', color='black', weight='bold')
    plt.text(ssi_66+0.01, 0.60, f'SSI = {ssi_66:.2f}', fontsize=7, ha='left', va='top', color='black')
    
    # Labels and legend
    plt.xlabel('SSI', fontsize=10)
    plt.ylabel('Cumulative Probability', fontsize=10)
    plt.legend(fontsize=7, loc='lower right')
    
    # Grid
    plt.minorticks_on()
    plt.grid(True, which='major', linestyle='--', alpha=0.5)
    plt.grid(True, which='minor', linestyle=':', alpha=0.3)
    
    # Limits
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    
    plt.tight_layout()
    
    if save_path:
        save_dir = os.path.dirname(save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
        plt.savefig(save_path, dpi=config.save_dpi, bbox_inches='tight')
    
    if show:
        plt.show()
    else:
        plt.close()


def plot_catchment_type_maps(
    season: str,
    gdf: gpd.GeoDataFrame,
    all_catchments_dormant_static: pd.DataFrame,
    all_catchments_growing_static: pd.DataFrame,
    region: Optional[str] = None,
    country_codes: Optional[List[str]] = None,
    extent: Optional[List[float]] = None,
    include_panels: bool = False,
    save: bool = False,
    save_dir: Optional[str] = None,
    show: bool = True,
    config: Optional[FigureConfig] = None,
    category_colors: Optional[Dict[str, str]] = None,
) -> None:
    """
    Plot catchment type maps for a given season and region.
    
    For global: saves as Figure S2 (only map, no panels)
    For regional: saves as Figure 1 (dormant) or Figure S3 (growing) with panels
    
    Saved files (when include_panels=True for regional maps):
    - Spatial_Distribution.png: Main map showing event type distribution
    - Longitudinal_Distribution.png: Bar chart showing distribution by longitude
    - Latitudinal_Distribution.png: Bar chart showing distribution by latitude
    - Type_Composition.png: Pie chart summarizing overall event type composition
    
    All files are saved directly to the region folder (e.g., Fig. 1/Europe/).
    
    Parameters:
    -----------
    season : str
        'dormant' or 'growing'
    region : str, optional
        Region name from DEFAULT_REGIONS. If None, uses global extent.
        If provided, extent and country_codes will be automatically set.
    include_panels : bool, default=False
        Whether to include longitude/latitude distribution and pie chart panels.
        For global maps, this should be False.
        For regional maps, this should be True.
    """
    if config is None:
        config = FigureConfig()
    
    if category_colors is None:
        category_colors = config.category_colors
    
    if season == 'dormant':
        df = all_catchments_dormant_static
    elif season == 'growing':
        df = all_catchments_growing_static
    else:
        raise ValueError("season must be 'dormant' or 'growing'")
    
    if region and region in DEFAULT_REGIONS:
        region_config = DEFAULT_REGIONS[region]
        if country_codes is None:
            country_codes = region_config.countries
        if extent is None:
            extent = region_config.range
        region_name = region_config.name
    else:
        # Global settings
        if extent is None:
            extent = DEFAULT_REGIONS['globe'].range
        if country_codes is None:
            country_codes = None  # All countries
        region_name = 'Global'
        include_panels = False  # Global maps don't have panels
    
    from pathlib import Path
    FIGURES_GENERATION_DIR = Path(__file__).parent.parent.resolve()
    
    if save_dir is None:
        if region is None or region == 'globe':
            save_dir = str(FIGURES_GENERATION_DIR / config.figures_base_path / 'Fig. S2')
        else:
            fig_num = 'Fig. 1' if season == 'dormant' else 'Fig. S3'
            save_dir = str(FIGURES_GENERATION_DIR / config.figures_base_path / fig_num / region_name)
    
    if save:
        os.makedirs(save_dir, exist_ok=True)
    
    if region is None or region == 'globe':
        figsize = config.default_figsize_global
        point_size = config.default_point_size
        linewidth = config.default_linewidth
    else:
        figsize = config.default_figsize_regional
        point_size = config.default_point_size
        linewidth = config.default_linewidth
    
    auto_adjust = (region is not None and region != 'globe')
    
    should_include_panels = include_panels and not show and save
    
    if region is None or region == 'globe':
        map_save_path = os.path.join(save_dir, f'Spatial_Distribution_{season}.png') if save else None
    else:
        map_save_path = os.path.join(save_dir, 'Spatial_Distribution.png') if save else None
    
    display_dpi_for_map = config.show_dpi if show else config.save_dpi
    plot_extent = plot_catchments_map(
        gdf=gdf,
        values=df[config.fig1_type_col],
        category_colors=category_colors,
        show_as_points=True,
        point_size=point_size,
        point_alpha=config.default_point_alpha,
        linewidth=linewidth,
        extent=extent,
        country_codes=country_codes,
        ignore_types=config.fig1_ignore_types,
        figsize=figsize,
        dpi=display_dpi_for_map,
        legend_loc=config.fig1_legend_loc if region else 'lower left',
        save=save,
        save_path=map_save_path,
        show=show,
        return_extent=should_include_panels,
        auto_adjust_figsize=auto_adjust,
        config=config,
    )
    
    if should_include_panels and plot_extent:
        if region is None or region == 'globe':
            # 2. Longitude distribution
            lon_save_path = os.path.join(save_dir, f'Longitudinal_Distribution_{season}.png') if save else None
            plot_distribution_by_axis(
                plot_extent, df, colors=category_colors, axis='lon',
                country_codes=country_codes, type_col=config.fig1_type_col,
                ignore_types=config.fig1_ignore_types, save=save, save_path=lon_save_path,
                show=False, config=config
            )
            
            lat_save_path = os.path.join(save_dir, f'Latitudinal_Distribution_{season}.png') if save else None
            plot_distribution_by_axis(
                plot_extent, df, colors=category_colors, axis='lat',
                country_codes=country_codes, type_col=config.fig1_type_col,
                ignore_types=config.fig1_ignore_types, save=save, save_path=lat_save_path,
                show=False, config=config
            )
            
            pie_save_path = os.path.join(save_dir, f'Type_Composition_{season}.png') if save else None
            plot_type_change_pie(
                df, colors=category_colors, country_codes=country_codes,
                type_col=config.fig1_type_col, ignore_types=config.fig1_ignore_types,
                save_path=pie_save_path, show=False, config=config
            )
        else:
            lon_save_path = os.path.join(save_dir, 'Longitudinal_Distribution.png') if save else None
            plot_distribution_by_axis(
                plot_extent, df, colors=category_colors, axis='lon',
                country_codes=country_codes, type_col=config.fig1_type_col,
                ignore_types=config.fig1_ignore_types, save=save, save_path=lon_save_path,
                show=False, config=config
            )
            
            # 3. Latitude distribution
            lat_save_path = os.path.join(save_dir, 'Latitudinal_Distribution.png') if save else None
            plot_distribution_by_axis(
                plot_extent, df, colors=category_colors, axis='lat',
                country_codes=country_codes, type_col=config.fig1_type_col,
                ignore_types=config.fig1_ignore_types, save=save, save_path=lat_save_path,
                show=False, config=config
            )
            
            # 4. Pie chart
            pie_save_path = os.path.join(save_dir, 'Type_Composition.png') if save else None
            plot_type_change_pie(
                df, colors=category_colors, country_codes=country_codes,
                type_col=config.fig1_type_col, ignore_types=config.fig1_ignore_types,
                save_path=pie_save_path, show=False, config=config  # Don't show individual panels
            )


def plot_distribution_by_axis(
    extent: Union[Dict[str, Tuple[float, float]], Dict],
    df: pd.DataFrame,
    colors: Dict[str, str],
    axis: str = 'lon',
    n_bins: Optional[int] = None,
    figsize: Optional[Tuple[float, float]] = None,
    dpi: int = 600,
    type_col: str = 'event_type_with_percentiles',
    country_codes: Optional[List[str]] = None,
    save: bool = False,
    save_path: Optional[str] = None,
    ignore_types: Optional[List[str]] = None,
    show: bool = True,
    config: Optional[FigureConfig] = None,
) -> None:
    """Plot distribution of catchment types by longitude or latitude."""
    from matplotlib.ticker import FuncFormatter
    
    if ignore_types is None:
        ignore_types = []
    elif isinstance(ignore_types, str):
        ignore_types = [ignore_types]
    
    def should_ignore_type(cat):
        return any(cat == ignore_type or cat.startswith(ignore_type + '-') for ignore_type in ignore_types)
    
    def format_lon(x):
        return f"{abs(x):.1f}°{'W' if x < 0 else 'E'}"
    
    def format_lat(x):
        return f"{abs(x):.1f}°{'S' if x < 0 else 'N'}"
    
    df_processed = df.copy()
    if country_codes and 'country' in df_processed.columns:
        df_processed = df_processed[df_processed['country'].isin(country_codes)]
    
    def extract_primary_type(s):
        return str(s).split('&')[0].split(':')[0].strip()
    
    df_processed['primary_type_clean'] = df_processed[type_col].astype(str).apply(extract_primary_type)
    type_col_for_stats = 'primary_type_clean'
    
    df_processed = df_processed[~df_processed[type_col_for_stats].apply(should_ignore_type)]
    
    if len(df_processed) == 0:
        print("Warning: No data after filtering")
        return
    
    # Handle extent format
    if isinstance(extent, dict):
        if 'x' in extent and 'y' in extent:
            lon_diff = abs(extent['x'][1] - extent['x'][0])
            lat_diff = abs(extent['y'][1] - extent['y'][0])
            x_min, x_max = extent['x']
            y_min, y_max = extent['y']
        else:
            raise ValueError("Invalid extent format. Expected dict with 'x' and 'y' keys.")
    else:
        raise ValueError("extent must be a dict")
    
    if figsize is None:
        if axis == 'lon':
            fig_x = lon_diff / lat_diff * 12
            figsize = (fig_x, 3)
            n_bins = int(lon_diff / 2) if n_bins is None else n_bins
        elif axis == 'lat':
            figsize = (3, 12)
            n_bins = int(lat_diff / 2) if n_bins is None else n_bins
        else:
            raise ValueError("axis must be 'lon' or 'lat'")
    
    if config is None:
        config = FigureConfig()
    
    display_dpi = config.show_dpi if show else config.save_dpi
    
    if axis == 'lon':
        if 'longitude' not in df_processed.columns:
            raise ValueError("DataFrame must contain 'longitude' column for axis='lon'")
        bins = np.linspace(x_min, x_max, n_bins+1)
        centers = (bins[:-1] + bins[1:]) / 2
        fig, ax = plt.subplots(figsize=figsize, dpi=display_dpi)
        bottom = np.zeros(n_bins)
        for cat in colors.keys():
            if cat not in df_processed[type_col_for_stats].unique():
                continue
            if should_ignore_type(cat):
                continue
            cat_data = df_processed[df_processed[type_col_for_stats] == cat]['longitude']
            if len(cat_data) == 0:
                continue
            counts = np.histogram(cat_data, bins=bins)[0]
            total = np.histogram(df_processed['longitude'], bins=bins)[0]
            proportions = np.divide(counts, total, out=np.zeros_like(counts, dtype=float), where=total>0) * 100
            ax.bar(centers, proportions, bottom=bottom, width=(bins[1]-bins[0])*0.8, color=colors[cat], alpha=0.7)
            bottom += proportions
        ax.set_xticks(centers)
        ax.set_xticklabels([format_lon(x) for x in centers], rotation=45)
        ax.set_xlim((x_min, x_max))
        ax.set_ylim(0, 100)
        ax.set_yticks([])
        ax.tick_params(axis='x', which='both', labelsize=14)
    elif axis == 'lat':
        if 'latitude' not in df_processed.columns:
            raise ValueError("DataFrame must contain 'latitude' column for axis='lat'")
        bins = np.linspace(y_min, y_max, n_bins+1)
        centers = (bins[:-1] + bins[1:]) / 2
        fig, ax = plt.subplots(figsize=figsize, dpi=display_dpi)
        left = np.zeros(n_bins)
        for cat in colors.keys():
            if cat not in df_processed[type_col_for_stats].unique():
                continue
            if should_ignore_type(cat):
                continue
            cat_data = df_processed[df_processed[type_col_for_stats] == cat]['latitude']
            if len(cat_data) == 0:
                continue
            counts = np.histogram(cat_data, bins=bins)[0]
            total = np.histogram(df_processed['latitude'], bins=bins)[0]
            proportions = np.divide(counts, total, out=np.zeros_like(counts, dtype=float), where=total>0) * 100
            ax.barh(centers, proportions, left=left, height=(bins[1]-bins[0])*0.8, color=colors[cat], alpha=0.7)
            left += proportions
        ax.set_yticks(centers)
        ax.set_yticklabels([format_lat(x) for x in centers])
        ax.set_xlim(0, 100)
        ax.set_ylim((y_min, y_max))
        ax.set_xticks([])
        ax.tick_params(axis='y', which='both', labelsize=14)
    else:
        raise ValueError("axis must be 'lon' or 'lat'")
    
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    
    if save and save_path is not None:
        save_dir = os.path.dirname(save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
        plt.savefig(save_path, dpi=config.save_dpi, bbox_inches='tight')
    
    if show:
        plt.show()
    else:
        plt.close()


def plot_type_change_pie(
    df: pd.DataFrame,
    type_col: str = 'event_type_with_percentiles',
    colors: Optional[Dict[str, str]] = None,
    country_codes: Optional[List[str]] = None,
    save_path: Optional[str] = None,
    dpi: int = 300,
    ignore_types: Optional[List[str]] = None,
    show: bool = True,
    config: Optional[FigureConfig] = None,
) -> None:
    """Plot pie chart of catchment type distribution."""
    if config is None:
        config = FigureConfig()
    
    if colors is None:
        colors = get_category_colors()
    
    if ignore_types is None:
        ignore_types = []
    elif isinstance(ignore_types, str):
        ignore_types = [ignore_types]
    
    def should_ignore_type(cat):
        return any(cat == ignore_type or cat.startswith(ignore_type + '-') for ignore_type in ignore_types)
    
    df_processed = df.copy()
    if country_codes and 'country' in df_processed.columns:
        df_processed = df_processed[df_processed['country'].isin(country_codes)]
    
    def extract_primary_type(s):
        return str(s).split('&')[0].split(':')[0].strip()
    
    df_processed['primary_type_clean'] = df_processed[type_col].astype(str).apply(extract_primary_type)
    type_col_for_stats = 'primary_type_clean'
    
    df_processed = df_processed[~df_processed[type_col_for_stats].apply(should_ignore_type)]
    
    if len(df_processed) == 0:
        print("Warning: No data after filtering")
        return
    
    value_counts = df_processed[type_col_for_stats].value_counts()
    sizes = value_counts.values
    color_list = [colors.get(label, '#cccccc') for label in value_counts.index]
    
    def autopct_format(pct):
        return ('%.1f%%' % pct) if pct >= 15 else ''
    
    display_dpi = config.show_dpi if show else config.save_dpi
    fig, ax = plt.subplots(figsize=(6, 6), dpi=display_dpi)
    wedges, texts, autotexts = ax.pie(
        sizes, labels=None, autopct=autopct_format, colors=color_list,
        startangle=90, textprops={'fontsize': 32}
    )
    for w in wedges:
        w.set_alpha(0.7)
    plt.tight_layout()
    
    if save_path:
        save_dir = os.path.dirname(save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
        plt.savefig(save_path, dpi=config.save_dpi, bbox_inches='tight')
    
    if show:
        plt.show()
    else:
        plt.close()



def create_metadata_with_consistency(
    event_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    consistency_col: str = 'consistency_index',
    type_col: str = 'primary_event_type',
) -> pd.DataFrame:
    """
    Create metadata with consistency and EMRI metrics.
    
    Parameters:
    -----------
    event_df : pd.DataFrame
        Event data with 'event_magnitude_response_index' column
    metadata_df : pd.DataFrame
        Metadata with consistency and type columns
    consistency_col : str
        Consistency column name
    type_col : str
        Type column name
    
    Returns:
    --------
    pd.DataFrame
        Metadata with EMRI mean and CV added
    """
    col = 'event_magnitude_response_index'
    
    grouped = event_df.groupby(event_df.index)[col]
    mean_values = grouped.mean()
    std_values = grouped.std()
    
    cv_values = (std_values / mean_values).replace([np.inf, -np.inf], np.nan)
    
    hr_df = pd.DataFrame({
        f'{col}_mean': mean_values,
        f'{col}_CV': cv_values
    })
    
    metadata_with_consistency = metadata_df.join(hr_df, how='inner')
    
    return metadata_with_consistency


def plot_coherence_consistency_heatmap(
    df: pd.DataFrame,
    coherency_col_daily: str = 'WI-Q_daily',
    coherency_col_weekly: str = 'WI-Q_weekly',
    consistency_col: str = 'consistency_index',
    type_col: str = 'primary_event_type',
    high_consistency_threshold: float = 0.9,
    figsize: Tuple[float, float] = (11, 4),
    cmap: str = 'Reds',
    save_path: Optional[str] = None,
    dpi: Optional[int] = None,
    show: bool = True,
    config: Optional[FigureConfig] = None,
) -> None:
    """
    Plot coherence vs consistency heatmap matrix.
    
    Figure 2: Flowpath Coherency Analysis
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing coherence columns (daily and weekly), consistency column, and type column
    coherency_col_daily : str, default='WI-Q_daily'
        Daily coherence column name
    coherency_col_weekly : str, default='WI-Q_weekly'
        Weekly coherence column name
    consistency_col : str, default='consistency_index'
        Consistency column name
    type_col : str, default='primary_event_type'
        Type column name
    high_consistency_threshold : float, default=0.9
        High consistency threshold
    figsize : Tuple[float, float], default=(11, 4)
        Figure size
    cmap : str, default='Reds'
        Color map
    save_path : Optional[str], default=None
        Save path. If None, figure is not saved.
    dpi : Optional[int], default=None
        DPI for saving. If None, uses config.save_dpi when saving.
    show : bool, default=True
        If True, display the figure with show_dpi. If False, only save with save_dpi.
    config : Optional[FigureConfig], default=None
        Configuration object. If None, uses default configuration.
    
    Returns:
    --------
    None
    """
    if config is None:
        config = FigureConfig()
    
    display_dpi = config.show_dpi if show else (dpi or config.save_dpi)
    save_dpi = dpi or config.save_dpi
    
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    rain_types = ['Rain-Dry', 'Rain-Mod', 'Rain-Wet']
    df_rain = df[df[type_col].isin(rain_types)].copy()
    
    bins = [0, 0.25, 0.5, 0.75, 1.0]
    bin_labels = [
        'Very\nweakly\ncoherent',
        'Weakly\ncoherent',
        'Moderately\ncoherent',
        'Strongly\ncoherent'
    ]
    
    daily_bin_labels = bin_labels
    weekly_bin_labels = bin_labels
    
    def create_heatmap_matrix(coherency_col):
        """
        Create heatmap matrix: each cell represents the number of high-consistency catchments
        for that (type×bin) combination as a percentage of the total number of high-consistency
        catchments within that type.
        """
        valid_data = df_rain[[coherency_col, consistency_col, type_col]].dropna().copy()
        high_consistency_data = valid_data[
            valid_data[consistency_col] >= high_consistency_threshold
        ].copy()
        
        if len(high_consistency_data) == 0:
            return np.zeros((3, 4))
        
        high_consistency_data.loc[:, 'coherence_bin'] = pd.cut(
            high_consistency_data[coherency_col],
            bins=bins,
            labels=bin_labels,
            include_lowest=True
        )
        
        matrix = []
        for rain_type in rain_types:
            type_data = high_consistency_data[high_consistency_data[type_col] == rain_type]
            type_count = len(type_data)
            row_pct = []
            for bin_label in bin_labels:
                if type_count > 0:
                    count = len(type_data[type_data['coherence_bin'] == bin_label])
                    row_pct.append(count / type_count * 100)
                else:
                    row_pct.append(0)
            matrix.append(row_pct)
        
        return np.array(matrix)
    
    matrix_daily = create_heatmap_matrix(coherency_col_daily)
    matrix_weekly = create_heatmap_matrix(coherency_col_weekly)
    
    row_labels = []
    for rain_type in rain_types:
        row_labels.append(f'{rain_type}')
    
    fig = plt.figure(figsize=figsize, dpi=display_dpi, constrained_layout=False)
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 0.1], hspace=0.05, wspace=0.3)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    cbar_ax = fig.add_subplot(gs[0, 2])
    
    vmax = max(matrix_daily.max(), matrix_weekly.max())
    vmin = 0
    
    max_tick = math.ceil(vmax / 5) * 5
    cbar_ticks = list(range(0, int(max_tick) + 1, 5))
    
    # Daily heatmap
    sns.heatmap(
        matrix_daily,
        annot=True,
        fmt='.1f',
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        cbar=False,
        ax=ax1,
        xticklabels=daily_bin_labels,
        yticklabels=row_labels,
        linewidths=0.5,
        linecolor='white'
    )
    ax1.set_title('(a) Daily frequency band', fontsize=12)
    ax1.set_yticklabels(row_labels, rotation=0, ha='right', va='center')
    ax1.set_xticklabels(daily_bin_labels, ha='center')
    
    # Weekly heatmap
    sns.heatmap(
        matrix_weekly,
        annot=True,
        fmt='.1f',
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        cbar_ax=cbar_ax,
        cbar_kws={
            'label': 'Proportion of catchments\nwithin each meteorological type (%)',
            'ticks': cbar_ticks,
            'format': '%.0f'
        },
        ax=ax2,
        xticklabels=weekly_bin_labels,
        yticklabels=row_labels,
        linewidths=0.5,
        linecolor='white'
    )
    ax2.set_title('(b) Weekly frequency band', fontsize=12)
    ax2.set_xticklabels(weekly_bin_labels, ha='center')
    ax2.set_yticks([])
    
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=UserWarning, message='.*tight_layout.*')
        try:
            fig.tight_layout()
        except Exception:
            plt.subplots_adjust(left=0.08, right=0.92, top=0.92, bottom=0.12, wspace=0.3)
    
    if save_path:
        plt.savefig(save_path, dpi=save_dpi, bbox_inches='tight', facecolor='white')
    
    if show:
        plt.show()
    else:
        plt.close(fig)


def plot_consistency_boxplot(
    metadata_df: pd.DataFrame,
    type_col: str = 'primary_event_type',
    consistency_col: str = 'consistency_index',
    figsize: Tuple[float, float] = (7, 2),
    title: Optional[str] = None,
    save_path: Optional[str] = None,
    dpi: int = 600,
    category_colors: Optional[Dict[str, str]] = None,
    show: bool = True,
    config: Optional[FigureConfig] = None,
) -> None:
    """
    Plot consistency boxplot by primary event type.
    
    Figure S4
    
    Parameters:
    -----------
    show : bool, default=True
        If True, display the figure with show_dpi. If False, only save with save_dpi.
    """
    if config is None:
        config = FigureConfig()
    
    display_dpi = config.show_dpi if show else config.save_dpi
    save_dpi = dpi or config.save_dpi
    
    if type_col not in metadata_df.columns:
        raise ValueError(f"Column '{type_col}' not found in metadata_df")
    if consistency_col not in metadata_df.columns:
        raise ValueError(f"Column '{consistency_col}' not found in metadata_df")
    
    type_data_dict = {}
    for type_name in metadata_df[type_col].dropna().unique():
        if type_name.startswith('Mixed-'):
            continue
        type_data = metadata_df[metadata_df[type_col] == type_name][consistency_col].dropna()
        if len(type_data) > 0:
            type_data_dict[type_name] = type_data.values
    
    ordered_types = []
    for prefix in ['Rain', 'ROS', 'Snow']:
        for suffix in ['Dry', 'Mod', 'Wet']:
            type_name = f'{prefix}-{suffix}'
            if type_name in type_data_dict:
                ordered_types.append(type_name)
    
    type_data_dict = {type_name: type_data_dict[type_name] for type_name in ordered_types}
    
    n_types = len(type_data_dict)
    n_cols = 3
    n_rows = (n_types + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(figsize[0] * n_cols / 3, figsize[1] * n_rows), dpi=display_dpi)
    if n_rows == 1:
        if n_cols == 1:
            axes = [axes]
        else:
            axes = list(axes) if isinstance(axes, np.ndarray) else [axes]
    else:
        axes = axes.flatten()
        axes = list(axes) if isinstance(axes, np.ndarray) else axes
    
    for idx, (type_name, data) in enumerate(type_data_dict.items()):
        ax = axes[idx]
        
        bp = ax.boxplot([data], tick_labels=[type_name], patch_artist=True, widths=0.5)
        
        if category_colors and type_name in category_colors:
            box_color = category_colors[type_name]
        else:
            colors = plt.cm.Set3(np.linspace(0, 1, n_types))
            box_color = colors[idx]
        
        for patch in bp['boxes']:
            patch.set_facecolor(box_color)
            patch.set_alpha(0.7)
        
        if idx % n_cols == 0:
            ax.set_ylabel('Consistency Index', fontsize=10)
            ax.tick_params(axis='y', labelsize=9)
        else:
            ax.set_ylabel('')
            ax.set_yticklabels([])
        
        ax.set_xlabel('')
        ax.set_xticklabels([])
        
        title_text = type_name.replace('-Mod', '-Moderate')
        ax.set_title(f'{title_text}', fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_ylim(0.35, 1.05)
    
    for idx in range(n_types, len(axes)):
        axes[idx].axis('off')
    
    plt.tight_layout()
    
    if save_path:
        save_dir = os.path.dirname(save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
        plt.savefig(save_path, dpi=config.save_dpi, bbox_inches='tight', facecolor='white')
    
    if show:
        plt.show()
    else:
        plt.close(fig)


def plot_magnitude_CV_by_coherency(
    df: pd.DataFrame,
    type_col: str = 'primary_event_type',
    consistency_col: str = 'consistency_index',
    consistency_threshold: float = 0.9,
    figsize: Tuple[float, float] = (15, 8),
    ylim_magnitude: Tuple[float, float] = (0, 4),
    y_max_threshold: float = 3,
    save_path: Optional[str] = None,
    dpi: int = 600,
    show: bool = True,
    config: Optional[FigureConfig] = None,
) -> None:
    """
    Plot Magnitude CV by coherency bins with violin plots.
    
    Figure 4
    
    Parameters:
    -----------
    show : bool, default=True
        If True, display the figure with show_dpi. If False, only save with save_dpi.
    """
    if config is None:
        config = FigureConfig()
    
    display_dpi = config.show_dpi if show else config.save_dpi
    save_dpi = dpi or config.save_dpi
    
    required_cols = [type_col, consistency_col, 'WI-Q_daily', 'WI-Q_weekly', 'event_magnitude_response_index_CV']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"DataFrame missing columns: {missing_cols}")
    
    df_filtered = df[df[consistency_col] > consistency_threshold].copy()
    
    if len(df_filtered) == 0:
        print(f"No data with consistency > {consistency_threshold}")
        return
    
    available_types = [t for t in df_filtered[type_col].dropna().unique() 
                        if not str(t).startswith('Mixed-')]
    
    rain_types = [t for t in available_types if t.startswith('Rain-')]
    if len(rain_types) >= 3:
        suffixes = ['Dry', 'Mod', 'Wet']
        rain_specific_types = [t for suffix in suffixes for t in rain_types if t.endswith(f'-{suffix}')][:3]
        types_to_plot = ['Rain-All'] + rain_specific_types
    else:
        raise ValueError(f"No enough Rain types to plot")
    
    coherency_bins = [0, 0.25, 0.5, 0.75, 1.0]
    coherency_bin_labels = [
        'Very\nweakly\ncoherent',
        'Weakly\ncoherent',
        'Moderately\ncoherent',
        'Strongly\ncoherent'
    ]
    
    daily_color = '#4A90E2'
    weekly_color = '#E24A4A'
    violin_edge_color = '#333333'
    
    n_rows = 2
    n_cols = len(types_to_plot)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(figsize[0] * n_cols / 4, figsize[1]), dpi=display_dpi)
    
    if n_rows == 1:
        axes = axes.reshape(1, -1)
    if n_cols == 1:
        axes = axes.reshape(-1, 1)
    axes = axes.flatten()
    
    coherency_cols = ['WI-Q_daily', 'WI-Q_weekly']
    coherency_names = ['Daily', 'Weekly']
    
    def plot_violin_single(ax, data_list, coherency_bin_labels, violin_color, violin_edge_color, y_max_threshold):
        width_per_bin = 0.6
        
        for bin_idx, bin_label in enumerate(coherency_bin_labels):
            if bin_idx >= len(data_list) or len(data_list[bin_idx]) == 0:
                continue
            
            data = np.array(data_list[bin_idx])
            position = bin_idx
            
            violin_drawn = False
            try:
                if len(data) >= 3:
                    kde = stats.gaussian_kde(data)
                    data_std = np.std(data)
                    y_min = data.min() - 2 * data_std
                    y_max = data.max() + 2 * data_std
                    y_range_extended = np.linspace(y_min, y_max, 200)
                    density_extended = kde(y_range_extended)
                    
                    max_density = density_extended.max()
                    if max_density > 0:
                        threshold = max_density * 0.01
                        valid_mask = density_extended >= threshold
                        if np.any(valid_mask):
                            valid_indices = np.where(valid_mask)[0]
                            y_range = y_range_extended[valid_indices[0]:valid_indices[-1]+1]
                            density = density_extended[valid_indices[0]:valid_indices[-1]+1]
                        else:
                            y_range = np.linspace(data.min(), data.max(), 100)
                            density = kde(y_range)
                            max_density = density.max()
                    else:
                        y_range = np.linspace(data.min(), data.max(), 100)
                        density = kde(y_range)
                        max_density = density.max()
                    
                    if max_density > 0:
                        density = density / max_density * width_per_bin * 0.4
                        
                        mask = y_range <= y_max_threshold
                        y_range_plot = y_range[mask]
                        density_plot = density[mask]
                        
                        if len(y_range_plot) > 0:
                            x_left = position - density_plot
                            ax.fill_betweenx(y_range_plot, position, x_left, 
                                            alpha=0.6, color=violin_color, linewidth=0)
                            ax.plot(x_left, y_range_plot, color=violin_edge_color, linewidth=0.5)
                            violin_drawn = True
                            
                            if np.any(y_range > y_max_threshold):
                                ax.fill_betweenx([y_max_threshold, ax.get_ylim()[1]], 
                                                position - width_per_bin * 0.5, position + width_per_bin * 0.5,
                                                color='white', linewidth=0, zorder=3)
                
                if violin_drawn:
                    q1 = np.percentile(data, 25)
                    median = np.median(data)
                    q3 = np.percentile(data, 75)
                    
                    if q1 <= y_max_threshold:
                        ax.plot([position - width_per_bin * 0.4, position], 
                               [q1, q1], color='black', linewidth=1.0, linestyle='--')
                    if median <= y_max_threshold:
                        ax.plot([position - width_per_bin * 0.4, position], 
                               [median, median], color='black', linewidth=1.5)
                    if q3 <= y_max_threshold:
                        ax.plot([position - width_per_bin * 0.4, position], 
                               [q3, q3], color='black', linewidth=1.0, linestyle='--')
                        
            except:
                pass
    
    def add_significance_brackets(ax, data_list, coherency_bin_labels, y_max_threshold, y_plot_max):
        """Add significance brackets above threshold region."""
        
        all_data_dict = {}
        for bin_idx, bin_label in enumerate(coherency_bin_labels):
            if bin_idx < len(data_list) and len(data_list[bin_idx]) > 0:
                data = np.array(data_list[bin_idx])
                if len(data) >= 3:
                    all_data_dict[bin_idx] = data
        
        comparisons = []
        all_bin_indices = list(range(len(coherency_bin_labels)))
        
        for i in range(len(all_bin_indices)):
            for j in range(i + 1, len(all_bin_indices)):
                bin1_idx = all_bin_indices[i]
                bin2_idx = all_bin_indices[j]
                
                data1 = all_data_dict.get(bin1_idx, np.array([]))
                data2 = all_data_dict.get(bin2_idx, np.array([]))
                
                if len(data1) >= 3 and len(data2) >= 3:
                    try:
                        statistic, p_value = stats.mannwhitneyu(data1, data2, alternative='two-sided')
                        comparisons.append({
                            'bin1': bin1_idx,
                            'bin2': bin2_idx,
                            'p_value': p_value
                        })
                    except:
                        pass
        
        if len(comparisons) == 0:
            return
        
        def get_significance_symbol(p):
            if p > 0.05:
                return 'ns'
            elif p <= 0.0001:
                return '****'
            elif p <= 0.001:
                return '***'
            elif p <= 0.01:
                return '**'
            else:
                return '*'
        
        def overlaps(comp1, comp2):
            """Check if two comparisons overlap (excluding adjacent comparisons)."""
            range1 = (min(comp1['bin1'], comp1['bin2']), max(comp1['bin1'], comp1['bin2']))
            range2 = (min(comp2['bin1'], comp2['bin2']), max(comp2['bin1'], comp2['bin2']))
            if range1[1] == range2[0] or range2[1] == range1[0]:
                return False
            return not (range1[1] < range2[0] or range2[1] < range1[0])
        
        distance1_comps = []
        distance2_comps = []
        distance3_comps = []
        
        for comp in comparisons:
            distance = comp['bin2'] - comp['bin1']
            if distance == 1:
                distance1_comps.append(comp)
            elif distance == 2:
                distance2_comps.append(comp)
            elif distance == 3:
                distance3_comps.append(comp)
        
        distance1_comps.sort(key=lambda x: x['bin1'])
        distance2_comps.sort(key=lambda x: x['bin1'])
        
        layers = [[] for _ in range(4)]
        
        layers[0] = distance1_comps.copy()
        
        if len(distance2_comps) > 1:
            layers[1].append(distance2_comps[1])
        
        if len(distance2_comps) > 0:
            layers[2].append(distance2_comps[0])
        
        if len(distance3_comps) > 0:
            layers[3].append(distance3_comps[0])
        
        layers = [layer for layer in layers if len(layer) > 0]
        
        y_axis_max = ax.get_ylim()[1]
        max_layers = len(layers)
        bracket_spacing = 0.2
        bracket_height = 0.02
        text_height = 0.03
        
        total_height_needed = max_layers * bracket_spacing + text_height
        bracket_y_base = min(y_max_threshold + 0.15, y_axis_max - total_height_needed + 0.15)
        
        for layer_idx, layer_comps in enumerate(layers):
            y_pos = bracket_y_base + layer_idx * bracket_spacing
            
            if y_pos > y_axis_max - 0.05:
                continue
            
            for comp in layer_comps:
                bin1_pos = comp['bin1']
                bin2_pos = comp['bin2']
                p_val = comp['p_value']
                sig_symbol = get_significance_symbol(p_val)
                
                bracket_height = 0.06
                ax.plot([bin1_pos, bin2_pos], [y_pos, y_pos], 
                       color='black', linewidth=1.0, zorder=15)
                ax.plot([bin1_pos, bin1_pos], [y_pos - bracket_height, y_pos], 
                       color='black', linewidth=1.0, zorder=15)
                ax.plot([bin2_pos, bin2_pos], [y_pos - bracket_height, y_pos], 
                       color='black', linewidth=1.0, zorder=15)
                
                text_x = (bin1_pos + bin2_pos) / 2
                text_y = y_pos + 0.02
                if sig_symbol in ['*', '**', '***', '****']:
                    text_y = y_pos - 0.04
                ax.text(text_x, text_y, sig_symbol, 
                       ha='center', va='bottom', fontsize=8, 
                       fontweight='bold', zorder=16)
    
    for row_idx in range(n_rows):
        period_name = coherency_names[row_idx]
        coherency_col = coherency_cols[row_idx]
        
        for col_idx in range(n_cols):
            ax = axes[row_idx * n_cols + col_idx]
            
            current_type = types_to_plot[col_idx]
            
            if current_type == 'Rain-All':
                rain_types = [t for t in df_filtered[type_col].dropna().unique() 
                             if str(t).startswith('Rain-')]
                type_data = df_filtered[df_filtered[type_col].isin(rain_types)].copy()
            else:
                type_data = df_filtered[df_filtered[type_col] == current_type].copy()
            
            data_list = []
            
            if len(type_data) == 0:
                ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
            else:
                df_plot = type_data.copy()
                df_plot.loc[:, 'coherency_bin'] = pd.cut(
                    df_plot[coherency_col],
                    bins=coherency_bins,
                    labels=coherency_bin_labels,
                    include_lowest=True
                )
                
                for bin_label in coherency_bin_labels:
                    bin_data = df_plot[df_plot['coherency_bin'] == bin_label]['event_magnitude_response_index_CV'].dropna()
                    if len(bin_data) > 0:
                        data_list.append(bin_data.values)
                    else:
                        data_list.append([])
                
                if len([d for d in data_list if len(d) > 0]) == 0:
                    ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
                else:
                    current_color = daily_color if row_idx == 0 else weekly_color
                    plot_violin_single(ax, data_list, coherency_bin_labels, current_color, violin_edge_color, y_max_threshold)
            
            ax.set_xlim(-0.5, len(coherency_bin_labels) - 0.5)
            ax.set_xticks(range(len(coherency_bin_labels)))
            ax.set_xticklabels(coherency_bin_labels, fontsize=9, rotation=0, ha='center')
            
            ax.set_ylim(ylim_magnitude)
            y_max = ylim_magnitude[1]
            
            if len(type_data) > 0 and len([d for d in data_list if len(d) > 0]) > 0:
                add_significance_brackets(ax, data_list, coherency_bin_labels, y_max_threshold, ylim_magnitude[1])
            
            y_ticks = np.arange(0, 3.5, 0.5)
            ax.set_yticks(y_ticks)
            
            if col_idx == 0:
                ax.set_ylabel('Coefficient of Variation', fontsize=11)
                y_min, y_max = ylim_magnitude
                y_label_pos = (1.5 - y_min) / (y_max - y_min)
                ax.yaxis.set_label_coords(-0.12, y_label_pos)
                ax.tick_params(axis='y', labelsize=9)
            else:
                ax.set_ylabel('')
                ax.set_yticklabels([])
            
            title_text = current_type.replace('Rain-Mod', 'Rain-Moderate')
            ax.set_title(title_text, fontsize=11, fontweight='bold', pad=10)
            ax.grid(True, alpha=0.3, axis='y', linestyle='--')
    
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=UserWarning, message='.*tight_layout.*')
        try:
            plt.tight_layout(rect=[0, 0, 1, 0.94], hspace=0.45)
        except Exception:
            plt.subplots_adjust(left=0.08, right=0.95, top=0.88, bottom=0.1, hspace=0.50, wspace=0.3)
    
    ax_first_row = axes[0]
    ax_second_row = axes[n_cols] if n_cols > 0 else axes[0]
    
    bbox_first = ax_first_row.get_position()
    y_first_row_title = bbox_first.y1 + 0.05
    
    bbox_second = ax_second_row.get_position()
    y_second_row_title = bbox_second.y1 + 0.05
    
    y_first_row_title = min(y_first_row_title, 0.98)
    y_second_row_title = min(y_second_row_title, 0.98)
    
    fig.text(0.5, y_first_row_title, '(a) Daily frequency band', 
             ha='center', va='bottom', fontsize=13, fontweight='bold', transform=fig.transFigure)
    fig.text(0.5, y_second_row_title, '(b) Weekly frequency band', 
             ha='center', va='bottom', fontsize=13, fontweight='bold', transform=fig.transFigure)
    
    if save_path:
        save_dir = os.path.dirname(save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
        plt.savefig(save_path, dpi=save_dpi, bbox_inches='tight', facecolor='white')
    
    if show:
        plt.show()
    else:
        plt.close(fig)


def plot_hydrologic_response_comparison(
    events_df: pd.DataFrame,
    category_colors: Dict[str, str],
    save_path: Optional[str] = None,
    show: bool = True,
    dpi: int = 600,
    config: Optional[FigureConfig] = None,
) -> None:
    """
    Plot hydrologic response comparison across event types.
    
    Figure 5
    
    Parameters:
    -----------
    show : bool, default=True
        If True, display the figure with show_dpi. If False, only save with save_dpi.
    """
    if config is None:
        config = FigureConfig()
    
    display_dpi = config.show_dpi if show else config.save_dpi
    save_dpi = dpi or config.save_dpi
    
    def ecdf_at_x(arr, x):
        """Return proportion P(X <= x), arr is 1D array (NaN removed)."""
        if arr.size == 0:
            return np.nan
        a = np.sort(arr)
        return np.searchsorted(a, x, side="right") / a.size

    def annotate_max_min(ax, x, y_dict, color_dict, dy=0.02, fmt=".2f"):
        """Annotate max/min values. y_dict: {label: yval}; color_dict: {label: color}"""
        y_dict = {k: v for k, v in y_dict.items() if np.isfinite(v)}
        if not y_dict:
            return

        lab_max = max(y_dict, key=y_dict.get)
        lab_min = min(y_dict, key=y_dict.get)
        y_max = y_dict[lab_max]
        y_min = y_dict[lab_min]
        color_max = color_dict.get(lab_max, "k")
        color_min = color_dict.get(lab_min, "k")

        ax.scatter(x, y_max, s=25, color=color_max, zorder=5, edgecolors='none', marker='o')
        ax.annotate(f"{format(y_max, fmt)}",
                    xy=(x, y_max), xytext=(0, 0), textcoords="offset points",
                    ha="right", va="bottom", color=color_max, fontsize=10)

        ax.scatter(x, y_min, s=25, color=color_min, zorder=5, edgecolors='none', marker='o')
        ax.annotate(f"{format(y_min, fmt)}",
                    xy=(x, y_min), xytext=(0, 0), textcoords="offset points",
                    ha="left", va="top", color=color_min, fontsize=10)

    def format_label(label):
        """Replace 'Mod' with 'Moderate' in labels."""
        if label == 'Mod':
            return 'Moderate'
        return label.replace('Mod:', 'Moderate:').replace('Mod-', 'Moderate-')

    events_data = events_df.copy()
    line_styles = {
        'Wet': dict(linestyle='-', linewidth=2),
        'Mod': dict(linestyle='--', linewidth=2),
        'Dry': dict(linestyle=':', linewidth=2)
    }
    precipitation_types = ['Rain', 'Snow', 'ROS']
    soil_moisture_states = ['Dry', 'Mod', 'Wet']

    fig = plt.figure(figsize=(18, 6), dpi=display_dpi)
    gs = GridSpec(2, 3, figure=fig, hspace=0.6, wspace=0.3)

    def set_common_labels(ax, is_first_col):
        ax.set_xlabel('EMRI', fontsize=12)
        if is_first_col:
            ax.set_ylabel('Cumulative Probability', fontsize=12)
        else:
            ax.set_ylabel(None)

    # Top row: by precipitation type
    for col_idx, precipitation_type in enumerate(precipitation_types):
        ax = fig.add_subplot(gs[0, col_idx])
        
        for soil_moisture_state in soil_moisture_states:
            event_type = f"{precipitation_type}-{soil_moisture_state}"
            type_data = events_data[events_data['event_type'] == event_type]
            if len(type_data) < 10:
                continue
            color = category_colors.get(event_type, '#CCCCCC')
            sns.ecdfplot(
                data=type_data['event_magnitude_response_index'],
                ax=ax, color=color, label=format_label(soil_moisture_state),
                complementary=False, stat="proportion",
                **line_styles[soil_moisture_state]
            )
        
        for x0 in [0.10, 0.20, 0.30]:
            yvals = {}
            colors = {}
            for sms in soil_moisture_states:
                event_type = f"{precipitation_type}-{sms}"
                s = events_data.loc[events_data['event_type'] == event_type, 'event_magnitude_response_index'].dropna().values
                if s.size == 0:
                    continue
                y = ecdf_at_x(s, x0)
                label = format_label(sms + ":")
                yvals[label] = y
                colors[label] = category_colors.get(event_type, '#CCCCCC')
            annotate_max_min(ax, x0, yvals, colors)
        
        set_common_labels(ax, is_first_col=(col_idx == 0))
        ax.set_title(f"Comparison by {precipitation_type}", fontsize=14)
        ax.set_xlim(-0.05, 0.50)
        ax.set_ylim(0, 1.06)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=11, loc='lower right')

    fig.text(0.5, 1, '(a) Comparisons of EMRI distributions across antecedent soil moisture states.', 
             ha='center', fontsize=14, fontweight='bold')

    # Bottom row: by soil moisture state
    for col_idx, soil_moisture_state in enumerate(soil_moisture_states):
        ax = fig.add_subplot(gs[1, col_idx])
        
        for precipitation_type in precipitation_types:
            event_type = f"{precipitation_type}-{soil_moisture_state}"
            type_data = events_data[events_data['event_type'] == event_type]
            if len(type_data) < 10:
                continue
            color = category_colors.get(event_type, '#CCCCCC')
            sns.ecdfplot(
                data=type_data['event_magnitude_response_index'],
                ax=ax, color=color, label=precipitation_type,
                complementary=False, stat="proportion",
                **line_styles[soil_moisture_state]
            )
        
        for x0 in [0.10, 0.20, 0.30]:
            yvals = {}
            colors = {}
            for precipitation_type in precipitation_types:
                event_type = f"{precipitation_type}-{soil_moisture_state}"
                s = events_data.loc[events_data['event_type'] == event_type, 'event_magnitude_response_index'].dropna().values
                if s.size == 0:
                    continue
                y = ecdf_at_x(s, x0)
                label = format_label(precipitation_type + ":")
                yvals[label] = y
                colors[label] = category_colors.get(event_type, '#CCCCCC')
            annotate_max_min(ax, x0, yvals, colors)
        
        set_common_labels(ax, is_first_col=(col_idx == 0))
        ax.set_title(f"Comparison by {format_label(soil_moisture_state)}", fontsize=14)
        ax.set_xlim(-0.05, 0.50)
        ax.set_ylim(0, 1.06)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=11, loc='lower right')

    fig.text(0.5, 0.47, '(b) Comparisons of EMRI distributions across water input types.', 
             ha='center', fontsize=14, fontweight='bold')

    fig.subplots_adjust(top=0.92, bottom=0.08, left=0.08, right=0.95)
    
    if save_path:
        save_dir = os.path.dirname(save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
        fig.savefig(save_path, dpi=save_dpi, bbox_inches='tight', facecolor='white')
    
    if show:
        plt.show()
    else:
        plt.close(fig)


def plot_seasonal_transition(
    seasonal_transition: pd.DataFrame,
    region_config: Optional[RegionConfig] = None,
    region_name: Optional[str] = None,
    category_colors: Optional[Dict[str, str]] = None,
    color_source: str = 'hollow',
    fig_height: float = 5,
    save_path: Optional[str] = None,
    show: bool = True,
    config: Optional[FigureConfig] = None,
) -> None:
    """
    Plot seasonal transition bar chart for a region.
    
    Figure 2: Seasonal Transition Analysis
    
    Parameters:
    -----------
    seasonal_transition : pd.DataFrame
        DataFrame with columns: 'dormant_type', 'growing_type', 'transition', 'sm_change', 'country'
    region_config : RegionConfig, optional
        Region configuration. If None, uses all data.
    region_name : str, optional
        Region name for title. If None, uses 'Global' or region_config.name
    category_colors : Dict[str, str], optional
        Color mapping for categories. If None, uses config.category_colors
    color_source : str, default='hollow'
        Color source for bars: 'hollow' (no fill), 'dormant' (use dormant type color), 'growing' (use growing type color)
    fig_height : float, default=5
        Figure height
    save_path : str, optional
        Save path for the figure
    show : bool, default=True
        If True, display the figure with show_dpi. If False, only save with save_dpi.
    config : FigureConfig, optional
        Configuration object
    """
    if config is None:
        config = FigureConfig()
    
    if category_colors is None:
        category_colors = config.category_colors
    
    region_data = seasonal_transition.copy()
    if region_config is not None:
        region_countries = region_config.countries
        if 'country' in region_data.columns:
            region_mask = region_data['country'].isin(region_countries)
            region_data = region_data[region_mask].copy()
    
    if len(region_data) == 0:
        print(f'No data for {region_name or "region"}')
        return
    
    increase_data = region_data[region_data['sm_change'] == 'increase']
    decrease_data = region_data[region_data['sm_change'] == 'decrease']
    stable_data = region_data[region_data['sm_change'] == 'stable']
    
    increase_transitions = increase_data['transition'].value_counts().sort_index()
    decrease_transitions = decrease_data['transition'].value_counts().sort_index()
    stable_transitions = stable_data['transition'].value_counts().sort_index()
    
    all_transitions = pd.concat([increase_transitions, decrease_transitions, stable_transitions]).index.unique()
    n_transitions = len(all_transitions)
    
    if n_transitions == 0:
        print(f'No transitions for {region_name or "region"}')
        return
    
    n_left = len(increase_transitions)
    n_stable = len(stable_transitions)
    n_right = len(decrease_transitions)
    total_bars = n_left + n_stable + n_right
    fig_width = max(8, total_bars * 0.8)
    
    display_dpi = config.show_dpi if show else config.save_dpi
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=display_dpi)
    
    left_transitions = increase_transitions.index.tolist()
    stable_transitions_list = stable_transitions.index.tolist()
    right_transitions = decrease_transitions.index.tolist()
    
    x_positions = []
    transition_labels = []
    bar_colors = []
    bar_values = []
    
    def get_bar_color(trans, color_source):
        if color_source == 'hollow':
            return 'none'
        elif color_source == 'dormant':
            dormant_type = trans.split(' to ')[0]
            return category_colors.get(dormant_type, 'gray')
        elif color_source == 'growing':
            growing_type = trans.split(' to ')[1]
            return category_colors.get(growing_type, 'gray')
        else:
            return 'gray'
    
    for i, trans in enumerate(left_transitions):
        x_positions.append(i)
        transition_labels.append(trans)
        bar_values.append(increase_transitions[trans])
        bar_colors.append(get_bar_color(trans, color_source))
    
    start_stable = n_left + 1
    for i, trans in enumerate(stable_transitions_list):
        x_positions.append(start_stable + i)
        transition_labels.append(trans)
        bar_values.append(stable_transitions[trans])
        bar_colors.append(get_bar_color(trans, color_source))
    
    if n_stable > 0:
        start_right = n_left + n_stable + 2
    else:
        start_right = n_left + 1
    for i, trans in enumerate(right_transitions):
        x_positions.append(start_right + i)
        transition_labels.append(trans)
        bar_values.append(decrease_transitions[trans])
        bar_colors.append(get_bar_color(trans, color_source))
    
    if color_source == 'hollow':
        bars = ax.bar(x_positions, bar_values, 
                     facecolor='none', edgecolor='black', linewidth=1.5, alpha=1.0)
    else:
        bars = ax.bar(x_positions, bar_values, 
                     color=bar_colors, alpha=0.7, edgecolor='black', linewidth=0.5)
    
    ax.set_yscale('log')
    
    if n_left > 0 and n_stable > 0:
        split_position_left = (n_left - 1 + n_left + 1) / 2
        ax.axvline(x=split_position_left, color='black', linewidth=2, linestyle='-', zorder=10)
    
    if n_stable > 0 and n_right > 0:
        split_position_right = (n_left + n_stable + n_left + n_stable + 2) / 2
        ax.axvline(x=split_position_right, color='black', linewidth=2, linestyle='-', zorder=10)
    
    if n_stable == 0 and n_left > 0 and n_right > 0:
        split_position = (n_left - 1 + n_left + 1) / 2
        ax.axvline(x=split_position, color='black', linewidth=2, linestyle='-', zorder=10)
    
    ax.set_xticks(x_positions)
    ax.set_xticklabels(transition_labels, rotation=45, ha='right', fontsize=11)
    
    title_text = region_name if region_name else 'Global'
    ax.set_title(f'{title_text}', 
                 fontsize=14, fontweight='bold', pad=30)
    ax.set_ylabel('Number of Catchments', fontsize=12)
    
    current_ylim = ax.get_ylim()
    ax.set_ylim(current_ylim[0], current_ylim[1] * 1.3)
    
    y_top = current_ylim[1] * 1.3
    
    if n_left > 0:
        x_center_left = (n_left - 1) / 2
        ax.text(x_center_left, y_top*1.6, 'SM Increase', 
                ha='center', va='top', fontsize=11)
    
    if n_stable > 0:
        x_center_stable = start_stable + (n_stable - 1) / 2
        ax.text(x_center_stable, y_top*1.6, 'SM Stable', 
                ha='center', va='top', fontsize=11)
    
    if n_right > 0:
        x_center_right = start_right + (n_right - 1) / 2
        ax.text(x_center_right, y_top*1.6, 'SM Decrease', 
                ha='center', va='top', fontsize=11)
    
    ax.grid(True, which='both', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    for i, (bar, value) in enumerate(zip(bars, bar_values)):
        if value > 0:
            ax.text(bar.get_x() + bar.get_width()/2, value * 1.05, 
                   str(int(value)), ha='center', va='bottom', fontsize=11)
    
    plt.tight_layout()
    
    if save_path:
        save_dir = os.path.dirname(save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
        plt.savefig(save_path, dpi=config.save_dpi, bbox_inches='tight')
    
    if show:
        plt.show()
    else:
        plt.close(fig)

