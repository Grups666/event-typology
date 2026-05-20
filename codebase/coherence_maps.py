"""Coherence map plotting utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import Normalize

from .config import DEFAULT_REGIONS, FigureConfig


REGION_KEYS = [
    "north_america",
    "south_america",
    "europe",
    "southern_africa",
    "oceania",
    "southeast_asia",
]


def _is_fig1_visible_type(value: object, ignore_types: list[str]) -> bool:
    if pd.isna(value):
        return False
    value_str = str(value)
    if " & " not in value_str and ":" in value_str:
        primary_type = value_str.split(":", 1)[0]
    elif " & " in value_str:
        try:
            primary_type = value_str.split(" & ", 1)[0].split(":", 1)[0]
        except IndexError:
            return False
    else:
        return False
    return not any(
        primary_type == ignore_type or primary_type.startswith(ignore_type + "-")
        for ignore_type in ignore_types
    )


def plot_coherence_map_overview(
    metadata_df: pd.DataFrame,
    season: str,
    save_path: Optional[str] = None,
    show: bool = False,
    config: Optional[FigureConfig] = None,
    coherency_col: str = "WI-Q_daily",
    consistency_threshold: Optional[float] = None,
    cmap: str = "turbo",
) -> None:
    """Plot six regional maps colored only by daily WI-Q coherence.

    The map uses the same regional country/type scope as Figure 1: catchments
    must belong to the configured region countries and must not be dominated by
    Mixed event types. `spatial_pattern` is not required and is not encoded in
    marker shape.
    """
    if config is None:
        config = FigureConfig()

    required_cols = [
        coherency_col,
        "longitude",
        "latitude",
        "country",
        config.fig1_type_col,
    ]
    if consistency_threshold is not None:
        required_cols.append("consistency_index")
    missing = [col for col in required_cols if col not in metadata_df.columns]
    if missing:
        raise KeyError(f"Missing required metadata columns: {missing}")

    df = metadata_df.copy()
    fig1_type_mask = df[config.fig1_type_col].apply(
        lambda value: _is_fig1_visible_type(value, config.fig1_ignore_types)
    )
    valid = (
        df[coherency_col].notna()
        & df["longitude"].notna()
        & df["latitude"].notna()
        & fig1_type_mask
    )
    if consistency_threshold is not None:
        valid &= df["consistency_index"] >= consistency_threshold
    df = df.loc[valid].copy()

    fig, axes = plt.subplots(
        3,
        2,
        figsize=(11.0, 11.6),
        subplot_kw={"projection": ccrs.PlateCarree()},
        constrained_layout=False,
    )
    norm = Normalize(vmin=0.0, vmax=1.0)
    last_scatter = None

    for idx, region_key in enumerate(REGION_KEYS):
        region = DEFAULT_REGIONS[region_key]
        extent = region.range
        ax = axes.ravel()[idx]
        ax.set_anchor("W")
        ax.set_extent(extent, crs=ccrs.PlateCarree())
        ax.add_feature(cfeature.OCEAN, facecolor=config.ocean_color, zorder=0)
        ax.add_feature(cfeature.LAND, facecolor=config.land_color, edgecolor="none", zorder=0)
        ax.add_feature(cfeature.BORDERS, linestyle=":", edgecolor=config.border_color, linewidth=0.45, zorder=1)
        ax.add_feature(cfeature.COASTLINE, edgecolor=config.coastline_color, linewidth=0.55, zorder=1)
        ax.add_feature(cfeature.LAKES, alpha=0.25, zorder=1)
        ax.add_feature(cfeature.RIVERS, alpha=0.20, zorder=1)

        sub = df[
            df["country"].isin(region.countries)
            & df["longitude"].between(extent[0], extent[1])
            & df["latitude"].between(extent[2], extent[3])
        ]
        if not sub.empty:
            last_scatter = ax.scatter(
                sub["longitude"],
                sub["latitude"],
                c=sub[coherency_col],
                cmap=cmap,
                norm=norm,
                s=8,
                marker="o",
                alpha=0.86,
                linewidths=0,
                transform=ccrs.PlateCarree(),
                zorder=3,
            )

        gl = ax.gridlines(draw_labels=True, linewidth=0.25, color="#8a8a8a", alpha=0.35, linestyle="--")
        gl.top_labels = False
        gl.right_labels = False
        gl.xlabel_style = {"size": 7}
        gl.ylabel_style = {"size": 7}
        ax.text(
            0.0,
            1.035,
            region.name,
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=10.5,
            weight="bold",
            zorder=10,
        )

    if last_scatter is None:
        raise ValueError(f"No valid catchments available for {season} coherence map.")
    cax = fig.add_axes([0.20, 0.045, 0.62, 0.018])
    cbar = fig.colorbar(last_scatter, cax=cax, orientation="horizontal", ticks=[0, 0.25, 0.5, 0.75, 1.0])
    cbar.set_label("WI-Q coherence at daily band", fontsize=10)
    cbar.ax.tick_params(labelsize=8)

    fig.subplots_adjust(left=0.065, right=0.985, top=0.955, bottom=0.105, hspace=0.24, wspace=0.10)
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=config.save_dpi, facecolor="white")
    if show:
        plt.show()
    else:
        plt.close(fig)
