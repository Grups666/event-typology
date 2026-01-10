"""
Utility functions for figure generation.
"""


def hex_interpolate(color1: str, color2: str, ratio: float = 0.5) -> str:
    """
    Interpolate between two hex colors.
    
    Parameters:
    -----------
    color1 : str
        First hex color (e.g., '#0066CC')
    color2 : str
        Second hex color (e.g., '#40E0D0')
    ratio : float, default=0.5
        Interpolation ratio (0.0 = color1, 1.0 = color2)
    
    Returns:
    --------
    str
        Interpolated hex color
    """
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def rgb_to_hex(rgb):
        return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
    
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    rgb_mid = tuple(rgb1[i] + (rgb2[i] - rgb1[i]) * ratio for i in range(3))
    return rgb_to_hex(rgb_mid)


def get_category_colors() -> dict:
    """
    Get the default category color mapping.
    
    Returns:
    --------
    dict
        Dictionary mapping category names to hex colors
    """
    return {
        'Snow-Wet': '#0066CC',
        'Snow-Mod': hex_interpolate('#0066CC', '#40E0D0', 0.5),
        'Snow-Dry': '#40E0D0',
        'Rain-Wet': '#CC0000',
        'Rain-Mod': '#FF6600',
        'Rain-Dry': '#FFA500',
        'ROS-Wet': '#6A0DAD',
        'ROS-Mod': hex_interpolate('#6A0DAD', '#FF69B4', 0.5),
        'ROS-Dry': '#ff69b4',
        'Mixed-Wet': '#666666',
        'Mixed-Mod': '#666666',
        'Mixed-Dry': '#666666',
    }


def get_season_colors() -> dict:
    """
    Get season-specific colors.
    
    Returns:
    --------
    dict
        Dictionary with season color keys
    """
    return {
        'dormant_color': '#AD1B26',
        'growing_color': '#2E8B57',
    }

