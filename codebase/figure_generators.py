"""
High-level figure generation functions.
These functions provide one-line interfaces to generate all figures.
"""

import os
from typing import Optional
from pathlib import Path

FIGURES_GENERATION_DIR = Path(__file__).parent.parent.resolve()

from .data_loader import get_data_loader
from .config import FigureConfig, DEFAULT_REGIONS
from .utils import get_category_colors, get_season_colors
from .plotters import (
    plot_ssi_cdf,
    plot_catchment_type_maps,
    plot_coherence_consistency_heatmap,
    plot_consistency_boxplot,
    plot_magnitude_CV_by_coherency,
    plot_hydrologic_response_comparison,
    plot_seasonal_transition,
)


def _get_figures_path(config: FigureConfig) -> Path:
    """Get the absolute path to the figures directory."""
    figures_base = Path(config.figures_base_path)
    if figures_base.is_absolute():
        return figures_base
    else:
        # Relative to figures_generation directory
        return FIGURES_GENERATION_DIR / figures_base


def generate_figure_s1(
    data_folder: str = '../../data/Global Data V0.3',
    save_path: Optional[str] = None,
    save: bool = True,
    show: bool = False,
    config: Optional[FigureConfig] = None,
) -> None:
    """
    Generate Figure S1: SSI CDF.
    
    Parameters:
    -----------
    data_folder : str
        Path to data folder
    save_path : str, optional
        Custom save path. If None, uses default from config
    save : bool, default=True
        Whether to save the figure. If False, only display (when show=True).
    show : bool, default=False
        If True, display the figure with show_dpi. If False, only save with save_dpi.
    config : FigureConfig, optional
        Configuration object. If None, uses default
    """
    if config is None:
        config = FigureConfig()
    
    loader = get_data_loader(data_folder)
    dormant_ssi, growing_ssi, all_ssi = loader.ssi_data
    
    # Get season colors
    season_colors = get_season_colors()
    
    final_save_path = None
    if save:
        if save_path is None:
            figures_path = _get_figures_path(config)
            final_save_path = str(figures_path / 'Fig. S1' / 'SSI_CDF.png')
        else:
            final_save_path = str(Path(save_path)) if Path(save_path).is_absolute() else str(FIGURES_GENERATION_DIR / save_path)
        
        save_dir = os.path.dirname(final_save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
    
    plot_ssi_cdf(
        dormant_ssi=dormant_ssi,
        growing_ssi=growing_ssi,
        all_ssi=all_ssi,
        dormant_color=season_colors['dormant_color'],
        growing_color=season_colors['growing_color'],
        save_path=final_save_path,
        show=show,
        config=config
    )

def generate_figure_s2(
    season: str = 'dormant',
    data_folder: str = '../../data/Global Data V0.3',
    save: bool = True,
    show: bool = False,
    config: Optional[FigureConfig] = None,
) -> None:
    """
    Generate Figure S3: Global catchment type map.
    
    Parameters:
    -----------
    season : str
        'dormant' or 'growing'
    data_folder : str
        Path to data folder
    save : bool
        Whether to save the figure
    show : bool, default=False
        If True, display the figure with show_dpi. If False, only save with save_dpi.
    config : FigureConfig, optional
        Configuration object
    """
    if config is None:
        config = FigureConfig()
    
    loader = get_data_loader(data_folder)
    
    plot_catchment_type_maps(
        season=season,
        gdf=loader.gdf,
        all_catchments_dormant_static=loader.metadata_dormant,
        all_catchments_growing_static=loader.metadata_growing,
        region=None,  # Global
        include_panels=False,  # No panels for global maps
        save=save,
        show=show,
        config=config,
        category_colors=config.category_colors
    )


def generate_figure_1(
    region: Optional[str] = None,
    season: str = 'dormant',
    data_folder: str = '../../data/Global Data V0.3',
    save: bool = True,
    show: bool = False,
    config: Optional[FigureConfig] = None,
) -> None:
    """
    Generate Figure 1: Regional catchment type maps (dormant season).
    
    Parameters:
    -----------
    region : str, optional
        Region name: 'oceania', 'southern_africa', 'europe', 'north_america', 'south_america', 'southeast_asia'
        If None, generates for all regions (saves without showing).
        If specified, shows for that region (does not save unless save=True).
    season : str
        'dormant' or 'growing' (growing season goes to Figure S3)
    data_folder : str
        Path to data folder
    save : bool
        Whether to save the figure. If False and region is specified, only display (when show=True).
    show : bool, default=False
        If True, display the figure with show_dpi. If False, only save with save_dpi.
        When region is specified, this controls whether to show.
    config : FigureConfig, optional
        Configuration object
    """
    if config is None:
        config = FigureConfig()
    
    loader = get_data_loader(data_folder)
    
    if region is not None:
        if region not in DEFAULT_REGIONS or region == 'globe':
            raise ValueError(f"Invalid region: {region}. Must be one of: oceania, southern_africa, europe, north_america, south_america, southeast_asia")
        
        plot_catchment_type_maps(
            season=season,
            gdf=loader.gdf,
            all_catchments_dormant_static=loader.metadata_dormant,
            all_catchments_growing_static=loader.metadata_growing,
            region=region,
            include_panels=save and not show,
            save=save,
            show=show,
            config=config,
            category_colors=config.category_colors
        )
    else:
        for region_key in config.default_regions:
            plot_catchment_type_maps(
                season=season,
                gdf=loader.gdf,
                all_catchments_dormant_static=loader.metadata_dormant,
                all_catchments_growing_static=loader.metadata_growing,
                region=region_key,
                include_panels=True,
                save=True,
                show=False,
                config=config,
                category_colors=config.category_colors
            )


def generate_figure_s3(
    region: Optional[str] = None,
    data_folder: str = '../../data/Global Data V0.3',
    save: bool = True,
    show: bool = False,
    config: Optional[FigureConfig] = None,
) -> None:
    """
    Generate Figure S3: Regional catchment type maps (growing season).
    
    Parameters:
    -----------
    region : str, optional
        Region name: 'oceania', 'southern_africa', 'europe', 'north_america', 'south_america', 'southeast_asia'
        If None, generates for all regions (saves without showing).
    data_folder : str
        Path to data folder
    save : bool
        Whether to save the figure
    show : bool, default=False
        If True, display the figure with show_dpi. If False, only save with save_dpi.
    config : FigureConfig, optional
        Configuration object
    """
    generate_figure_1(region=region, season='growing', data_folder=data_folder, save=save, show=show, config=config)


def generate_figure_2(
    region: Optional[str] = None,
    data_folder: str = '../../data/Global Data V0.3',
    color_source: str = 'hollow',
    save: bool = True,
    show: bool = False,
    config: Optional[FigureConfig] = None,
) -> None:
    """
    Generate Figure 2: Seasonal transition analysis.
    
    Parameters:
    -----------
    region : str, optional
        Region name: 'oceania', 'southern_africa', 'europe', 'north_america', 'south_america', 'southeast_asia'
        If None, generates for all regions (saves without showing).
        If specified, shows for that region (does not save unless save=True).
    data_folder : str
        Path to data folder
    color_source : str, default='hollow'
        Color source for bars: 'hollow' (no fill), 'dormant' (use dormant type color), 'growing' (use growing type color)
    save : bool, default=True
        Whether to save the figure. If False and region is specified, only display (when show=True).
    show : bool, default=False
        If True, display the figure with show_dpi. If False, only save with save_dpi.
        When region is specified, this controls whether to show.
    config : FigureConfig, optional
        Configuration object
    """
    import pandas as pd
    
    if config is None:
        config = FigureConfig()
    
    loader = get_data_loader(data_folder)
    metadata_dormant = loader.metadata_dormant
    metadata_growing = loader.metadata_growing
    
    dormant_types = metadata_dormant[['primary_event_type']].copy()
    dormant_types.columns = ['dormant_type']
    dormant_types.index.name = 'GCIN'
    
    growing_types = metadata_growing[['primary_event_type']].copy()
    growing_types.columns = ['growing_type']
    growing_types.index.name = 'GCIN'
    
    seasonal_transition = dormant_types.join(growing_types, how='inner')
    seasonal_transition['transition'] = seasonal_transition['dormant_type'].astype(str) + ' to ' + seasonal_transition['growing_type'].astype(str)
    
    if 'country' not in seasonal_transition.columns:
        if 'country' in metadata_dormant.columns:
            seasonal_transition = seasonal_transition.join(metadata_dormant[['country']], how='left')
        elif 'country' in metadata_growing.columns:
            seasonal_transition = seasonal_transition.join(metadata_growing[['country']], how='left')
    
    sm_levels = {'Dry': 1, 'Mod': 2, 'Wet': 3}
    
    def get_sm_level(catchment_type):
        """Extract SM state (dry/mod/wet) from catchment_type."""
        if pd.isna(catchment_type):
            return None
        for sm_state in ['Dry', 'Mod', 'Wet']:
            if sm_state in str(catchment_type):
                return sm_state
        return None
    
    def get_sm_change(dormant_type, growing_type):
        """Determine if SM increases, decreases, or remains stable."""
        dormant_sm = get_sm_level(dormant_type)
        growing_sm = get_sm_level(growing_type)
        
        if dormant_sm is None or growing_sm is None:
            return None
        
        dormant_level = sm_levels.get(dormant_sm, 0)
        growing_level = sm_levels.get(growing_sm, 0)
        
        if growing_level > dormant_level:
            return 'increase'
        elif growing_level < dormant_level:
            return 'decrease'
        else:
            return 'stable'
    
    seasonal_transition['sm_change'] = seasonal_transition.apply(
        lambda row: get_sm_change(row['dormant_type'], row['growing_type']), axis=1
    )
    
    if region is not None:
        if region not in DEFAULT_REGIONS or region == 'globe':
            raise ValueError(f"Invalid region: {region}. Must be one of: oceania, southern_africa, europe, north_america, south_america, southeast_asia")
        
        region_config = DEFAULT_REGIONS[region]
        region_name = region_config.name
        
        final_save_path = None
        if save:
            figures_path = _get_figures_path(config)
            final_save_path = str(figures_path / 'Fig. 2' / f'{region_name}_Seasonal_Transition.png')
        
        plot_seasonal_transition(
            seasonal_transition=seasonal_transition,
            region_config=region_config,
            region_name=region_name,
            category_colors=config.category_colors,
            color_source=color_source,
            save_path=final_save_path,
            show=show,
            config=config
        )
    else:
        figures_path = _get_figures_path(config)
        for region_key in config.default_regions:
            region_config = DEFAULT_REGIONS[region_key]
            region_name = region_config.name
            final_save_path = str(figures_path / 'Fig. 2' / f'{region_name}_Seasonal_Transition.png')
            plot_seasonal_transition(
                seasonal_transition=seasonal_transition,
                region_config=region_config,
                region_name=region_name,
                category_colors=config.category_colors,
                color_source=color_source,
                save_path=final_save_path,
                show=False,
                config=config
            )


def generate_figure_3(
    season: str = 'dormant',
    data_folder: str = '../../data/Global Data V0.3',
    save_path: Optional[str] = None,
    save: bool = True,
    show: bool = False,
    config: Optional[FigureConfig] = None,
) -> None:
    """
    Generate Figure 3: Coherence Consistency Heatmap.
    
    Parameters:
    -----------
    season : str
        'dormant' or 'growing' (growing season might go to Figure S5)
    data_folder : str
        Path to data folder
    save_path : str, optional
        Custom save path
    save : bool, default=True
        Whether to save the figure. If False, only display (when show=True).
    show : bool, default=False
        If True, display the figure with show_dpi. If False, only save with save_dpi.
    config : FigureConfig, optional
        Configuration object
    """
    if config is None:
        config = FigureConfig()
    
    loader = get_data_loader(data_folder)
    metadata = loader.metadata_dormant if season == 'dormant' else loader.metadata_growing
    
    final_save_path = None
    if save:
        if save_path is None:
            fig_num = 'Fig. 3' if season == 'dormant' else 'Fig. S5'
            final_save_path = str(_get_figures_path(config) / fig_num / f'Heatmap_Coherence_Consistency_{season}.png')
        else:
            final_save_path = str(Path(save_path)) if Path(save_path).is_absolute() else str(FIGURES_GENERATION_DIR / save_path)
        
        save_dir = os.path.dirname(final_save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
    
    plot_coherence_consistency_heatmap(
        df=metadata,
        save_path=final_save_path,
        show=show,
        config=config
    )


def generate_figure_s4(
    season: str = 'dormant',
    data_folder: str = '../../data/Global Data V0.3',
    save_path: Optional[str] = None,
    save: bool = True,
    show: bool = False,
    config: Optional[FigureConfig] = None,
) -> None:
    """
    Generate Figure S4: Consistency Boxplot.
    
    Parameters:
    -----------
    season : str
        'dormant' or 'growing'
    data_folder : str
        Path to data folder
    save_path : str, optional
        Custom save path
    save : bool, default=True
        Whether to save the figure. If False, only display (when show=True).
    show : bool, default=False
        If True, display the figure with show_dpi. If False, only save with save_dpi.
    config : FigureConfig, optional
        Configuration object
    """
    if config is None:
        config = FigureConfig()
    
    loader = get_data_loader(data_folder)
    metadata = loader.metadata_dormant if season == 'dormant' else loader.metadata_growing
    
    final_save_path = None
    if save:
        if save_path is None:
            final_save_path = str(_get_figures_path(config) / 'Fig. S4' / f'Consistency_Boxplot_{season}.png')
        else:
            final_save_path = str(Path(save_path)) if Path(save_path).is_absolute() else str(FIGURES_GENERATION_DIR / save_path)
        
        save_dir = os.path.dirname(final_save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
    
    plot_consistency_boxplot(
        metadata_df=metadata,
        save_path=final_save_path,
        category_colors=config.category_colors,
        show=show,
        config=config
    )


def generate_figure_4(
    season: str = 'dormant',
    data_folder: str = '../../data/Global Data V0.3',
    save_path: Optional[str] = None,
    save: bool = True,
    show: bool = False,
    config: Optional[FigureConfig] = None,
) -> None:
    """
    Generate Figure 4: Magnitude CV by Coherency (dormant season).
    Growing season goes to Figure S6.
    
    Parameters:
    -----------
    season : str
        'dormant' or 'growing'
    data_folder : str
        Path to data folder
    save_path : str, optional
        Custom save path
    save : bool, default=True
        Whether to save the figure. If False, only display (when show=True).
    show : bool, default=False
        If True, display the figure with show_dpi. If False, only save with save_dpi.
    config : FigureConfig, optional
        Configuration object
    """
    if config is None:
        config = FigureConfig()
    
    loader = get_data_loader(data_folder)
    metadata = loader.metadata_dormant if season == 'dormant' else loader.metadata_growing
    events = loader.event_dormant if season == 'dormant' else loader.event_growing
    
    from .plotters import create_metadata_with_consistency
    metadata_with_emri = create_metadata_with_consistency(events, metadata)
    
    final_save_path = None
    if save:
        if save_path is None:
            fig_num = 'Fig. 4' if season == 'dormant' else 'Fig. S6'
            final_save_path = str(_get_figures_path(config) / fig_num / f'Mag_CV_Vs_Coherency_{season}.png')
        else:
            final_save_path = str(Path(save_path)) if Path(save_path).is_absolute() else str(FIGURES_GENERATION_DIR / save_path)
        
        save_dir = os.path.dirname(final_save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
    
    plot_magnitude_CV_by_coherency(
        df=metadata_with_emri,
        save_path=final_save_path,
        show=show,
        config=config
    )


def generate_figure_s6(
    data_folder: str = '../../data/Global Data V0.3',
    save_path: Optional[str] = None,
    save: bool = True,
    show: bool = False,
    config: Optional[FigureConfig] = None,
) -> None:
    """Generate Figure S6: Magnitude CV by Coherency (growing season)."""
    generate_figure_4(season='growing', data_folder=data_folder, save_path=save_path, save=save, show=show, config=config)


def generate_figure_5(
    season: str = 'dormant',
    data_folder: str = '../../data/Global Data V0.3',
    save_path: Optional[str] = None,
    save: bool = True,
    show: bool = False,
    config: Optional[FigureConfig] = None,
) -> None:
    """
    Generate Figure 5: Hydrologic Response Comparison.
    Growing season goes to Figure S7.
    
    Parameters:
    -----------
    season : str
        'dormant' or 'growing'
    data_folder : str
        Path to data folder
    save_path : str, optional
        Custom save path
    save : bool, default=True
        Whether to save the figure. If False, only display (when show=True).
    show : bool, default=False
        If True, display the figure with show_dpi. If False, only save with save_dpi.
    config : FigureConfig, optional
        Configuration object
    """
    if config is None:
        config = FigureConfig()
    
    loader = get_data_loader(data_folder)
    events = loader.event_dormant if season == 'dormant' else loader.event_growing
    
    final_save_path = None
    if save:
        if save_path is None:
            fig_num = 'Fig. 5' if season == 'dormant' else 'Fig. S7'
            final_save_path = str(_get_figures_path(config) / fig_num / 'Mag_Comparison_Combined_CDF.png')
        else:
            final_save_path = str(Path(save_path)) if Path(save_path).is_absolute() else str(FIGURES_GENERATION_DIR / save_path)
        
        save_dir = os.path.dirname(final_save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
    
    plot_hydrologic_response_comparison(
        events_df=events,
        category_colors=config.category_colors,
        save_path=final_save_path,
        show=show,
        config=config
    )


def generate_figure_s7(
    data_folder: str = '../../data/Global Data V0.3',
    save_path: Optional[str] = None,
    save: bool = True,
    show: bool = False,
    config: Optional[FigureConfig] = None,
) -> None:
    """Generate Figure S7: Hydrologic Response Comparison (growing season)."""
    generate_figure_5(season='growing', data_folder=data_folder, save_path=save_path, save=save, show=show, config=config)


def generate_all_figures(
    data_folder: str = '../../data/Global Data V0.3',
    regions: Optional[list] = None,
    show: bool = False,
    config: Optional[FigureConfig] = None,
) -> None:
    """
    Generate all figures.
    
    Parameters:
    -----------
    data_folder : str
        Path to data folder
    regions : list, optional
        List of regions to generate. If None, generates all regions
    show : bool, default=False
        If True, display figures with show_dpi. If False, only save with save_dpi.
    config : FigureConfig, optional
        Configuration object
    """
    if config is None:
        config = FigureConfig()
    
    if regions is None:
        regions = config.default_regions
    
    # Figure S1
    print("Generating Figure S1...")
    generate_figure_s1(data_folder=data_folder, show=show, config=config)
    
    # Figure S2 (Global maps)
    print("Generating Figure S2 (Global maps)...")
    for season in ['dormant', 'growing']:
        generate_figure_s2(season=season, data_folder=data_folder, show=show, config=config)
    
    # Figure 1 and S3 (Regional maps)
    print("Generating Figure 1 and S3 (Regional maps)...")
    for season in ['dormant', 'growing']:
        if season == 'dormant':
            generate_figure_1(region=None, season=season, data_folder=data_folder, show=show, config=config)
        else:
            generate_figure_s3(region=None, data_folder=data_folder, show=show, config=config)
    
    # Figure 2 (Seasonal transitions)
    print("Generating Figure 2 (Seasonal transitions)...")
    generate_figure_2(region=None, data_folder=data_folder, show=show, config=config)
    
    # Figure 3 and S5 (Coherence heatmaps)
    print("Generating Figure 3 and S5 (Coherence heatmaps)...")
    for season in ['dormant', 'growing']:
        generate_figure_3(season=season, data_folder=data_folder, show=show, config=config)
    
    # Figure S4
    print("Generating Figure S4 (Consistency boxplots)...")
    for season in ['dormant', 'growing']:
        generate_figure_s4(season=season, data_folder=data_folder, show=show, config=config)
    
    # Figure 4 and S6
    print("Generating Figure 4 and S6 (Magnitude CV)...")
    for season in ['dormant', 'growing']:
        generate_figure_4(season=season, data_folder=data_folder, show=show, config=config)
    
    # Figure 5 and S7
    print("Generating Figure 5 and S7 (Hydrologic response)...")
    for season in ['dormant', 'growing']:
        generate_figure_5(season=season, data_folder=data_folder, show=show, config=config)
    
    print("All figures generated!")

