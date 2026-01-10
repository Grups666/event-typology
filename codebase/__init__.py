"""
Figures Generation Module
A modular package for generating publication-quality figures.
"""

__version__ = "0.1.0"

from .config import FigureConfig, RegionConfig
from .utils import hex_interpolate, get_category_colors, get_season_colors
from .data_loader import DataLoader, get_data_loader
from .figure_generators import (
    generate_figure_s1,
    generate_figure_s2,
    generate_figure_1,
    generate_figure_s3,
    generate_figure_2,
    generate_figure_3,
    generate_figure_s4,
    generate_figure_4,
    generate_figure_s6,
    generate_figure_5,
    generate_figure_s7,
    generate_all_figures,
)

__all__ = [
    'FigureConfig',
    'RegionConfig',
    'DataLoader',
    'get_data_loader',
    'get_category_colors',
    'get_season_colors',
    'generate_figure_s1',
    'generate_figure_s2',
    'generate_figure_1',
    'generate_figure_s3',
    'generate_figure_2',
    'generate_figure_3',
    'generate_figure_s4',
    'generate_figure_4',
    'generate_figure_s6',
    'generate_figure_5',
    'generate_figure_s7',
    'generate_all_figures',
]

