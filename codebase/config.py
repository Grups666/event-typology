"""
Configuration module for figure generation.
Centralizes all configuration parameters for easy modification.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class RegionConfig:
    """Configuration for geographic regions."""
    countries: List[str]
    range: List[float]
    name: str


@dataclass
class FigureConfig:
    """Centralized configuration for all figures."""
    
    category_colors: Dict[str, str] = None
    
    default_figsize_global: Tuple[float, float] = (40, 28)
    default_figsize_regional: Tuple[float, float] = (20, 12)
    default_point_size: float = 30
    default_linewidth: float = 1.5
    default_point_alpha: float = 0.7
    
    show_dpi: int = 100
    save_dpi: int = 300
    
    ocean_color: str = '#e6f2ff'
    land_color: str = 'whitesmoke'
    border_color: str = 'black'
    coastline_color: str = 'black'
    lake_alpha: float = 0.3
    river_alpha: float = 0.3
    
    catchment_edgecolor: str = 'indianred'
    catchment_facecolor: str = 'mistyrose'
    catchment_linewidth: float = 0.3
    
    fig1_ignore_types: List[str] = None
    fig1_type_col: str = 'event_type_with_percentiles'
    fig1_legend_loc: str = 'lower left'
    
    figures_base_path: str = 'figures'
    default_regions: List[str] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.category_colors is None:
            from .utils import get_category_colors
            self.category_colors = get_category_colors()
        
        if self.fig1_ignore_types is None:
            self.fig1_ignore_types = ['Mixed']
        
        if self.default_regions is None:
            self.default_regions = [
                'oceania', 'southern_africa', 'europe', 
                'north_america', 'south_america', 'southeast_asia'
            ]


DEFAULT_REGIONS = {
    'globe': RegionConfig(
        countries=['all'],
        range=[-180, 180, -60, 65],
        name='Globe'
    ),
    'oceania': RegionConfig(
        countries=['AU', 'NZ'],
        range=[110.0, 180.0, -50.0, -8.0],
        name='Oceania'
    ),
    'southern_africa': RegionConfig(
        countries=['ZA', 'ZW', 'ZM', 'BW', 'LS', 'SZ', 'MZ', 'MW', 'TZ'],
        range=[10.0, 42.0, -38.0, 0.0],
        name='Southern Africa'
    ),
    'europe': RegionConfig(
        countries=['GB', 'IE', 'FR', 'DK', 'DE', 'CH', 'IT', 'SI', 'AT', 'HU', 'SE'],
        range=[-13.0, 20.0, 40.0, 60.0],
        name='Europe'
    ),
    'north_america': RegionConfig(
        countries=['CA', 'US', 'MX'],
        range=[-140, -50, 12, 65],
        name='North America'
    ),
    'south_america': RegionConfig(
        countries=['CL', 'BR', 'AR', 'CO', 'EC', 'GF', 'GY', 'UY', 'VE'],
        range=[-85, -30, -60, 12],
        name='South America'
    ),
    'southeast_asia': RegionConfig(
        countries=['ID', 'MY', 'SG', 'TH', 'VN', 'PH', 'MM', 'KH', 'LA', 'BN', 'TL'],
        range=[90.0, 130.0, -12.0, 23.0],
        name='Southeast Asia'
    ),
}

