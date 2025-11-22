"""
Color Utility Functions
RGB to Lab conversion, Delta-E calculations
"""

import numpy as np
from typing import Tuple


def rgb_to_lab(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
    """
    Convert RGB to Lab color space
    
    Lab color space is designed to approximate human vision.
    L: Lightness (0-100)
    a: Green to Red (-128 to +127)
    b: Blue to Yellow (-128 to +127)
    
    Args:
        rgb: RGB tuple (0-255)
        
    Returns:
        Lab tuple (L, a, b)
    """
    # Normalize RGB
    r, g, b = [x / 255.0 for x in rgb]
    
    # Convert to linear RGB
    def gamma_correction(channel):
        if channel > 0.04045:
            return ((channel + 0.055) / 1.055) ** 2.4
        else:
            return channel / 12.92
    
    r = gamma_correction(r)
    g = gamma_correction(g)
    b = gamma_correction(b)
    
    # Convert to XYZ
    x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
    y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041
    
    # Normalize for D65 illuminant
    x = x / 0.95047
    y = y / 1.00000
    z = z / 1.08883
    
    # Convert to Lab
    def xyz_to_lab(t):
        if t > 0.008856:
            return t ** (1/3)
        else:
            return (7.787 * t) + (16 / 116)
    
    fx = xyz_to_lab(x)
    fy = xyz_to_lab(y)
    fz = xyz_to_lab(z)
    
    L = (116 * fy) - 16
    a = 500 * (fx - fy)
    b_val = 200 * (fy - fz)
    
    return (L, a, b_val)


def calculate_delta_e_2000(lab1: Tuple[float, float, float], 
                           lab2: Tuple[float, float, float]) -> float:
    """
    Calculate Delta-E using CIE2000 formula
    Most accurate method for perceptual color difference
    
    Args:
        lab1: First Lab color (L, a, b)
        lab2: Second Lab color (L, a, b)
        
    Returns:
        Delta-E value (0-100)
    """
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2
    
    # Calculate C and h
    C1 = np.sqrt(a1**2 + b1**2)
    C2 = np.sqrt(a2**2 + b2**2)
    
    C_bar = (C1 + C2) / 2
    
    G = 0.5 * (1 - np.sqrt(C_bar**7 / (C_bar**7 + 25**7)))
    
    a1_prime = (1 + G) * a1
    a2_prime = (1 + G) * a2
    
    C1_prime = np.sqrt(a1_prime**2 + b1**2)
    C2_prime = np.sqrt(a2_prime**2 + b2**2)
    
    h1_prime = np.arctan2(b1, a1_prime) % (2 * np.pi)
    h2_prime = np.arctan2(b2, a2_prime) % (2 * np.pi)
    
    # Calculate deltas
    delta_L_prime = L2 - L1
    delta_C_prime = C2_prime - C1_prime
    
    if C1_prime * C2_prime == 0:
        delta_h_prime = 0
    else:
        delta_h = h2_prime - h1_prime
        if abs(delta_h) <= np.pi:
            delta_h_prime = delta_h
        elif delta_h > np.pi:
            delta_h_prime = delta_h - 2 * np.pi
        else:
            delta_h_prime = delta_h + 2 * np.pi
    
    delta_H_prime = 2 * np.sqrt(C1_prime * C2_prime) * np.sin(delta_h_prime / 2)
    
    # Calculate means
    L_bar_prime = (L1 + L2) / 2
    C_bar_prime = (C1_prime + C2_prime) / 2
    
    if C1_prime * C2_prime == 0:
        h_bar_prime = h1_prime + h2_prime
    else:
        if abs(h1_prime - h2_prime) <= np.pi:
            h_bar_prime = (h1_prime + h2_prime) / 2
        elif h1_prime + h2_prime < 2 * np.pi:
            h_bar_prime = (h1_prime + h2_prime + 2 * np.pi) / 2
        else:
            h_bar_prime = (h1_prime + h2_prime - 2 * np.pi) / 2
    
    T = (1 - 0.17 * np.cos(h_bar_prime - np.pi/6) +
         0.24 * np.cos(2 * h_bar_prime) +
         0.32 * np.cos(3 * h_bar_prime + np.pi/30) -
         0.20 * np.cos(4 * h_bar_prime - 63 * np.pi/180))
    
    delta_theta = (np.pi/6) * np.exp(-((h_bar_prime - 275 * np.pi/180) / (25 * np.pi/180))**2)
    
    R_C = 2 * np.sqrt(C_bar_prime**7 / (C_bar_prime**7 + 25**7))
    
    S_L = 1 + ((0.015 * (L_bar_prime - 50)**2) / np.sqrt(20 + (L_bar_prime - 50)**2))
    S_C = 1 + 0.045 * C_bar_prime
    S_H = 1 + 0.015 * C_bar_prime * T
    
    R_T = -np.sin(2 * delta_theta) * R_C
    
    # Final Delta-E 2000
    delta_e = np.sqrt(
        (delta_L_prime / S_L)**2 +
        (delta_C_prime / S_C)**2 +
        (delta_H_prime / S_H)**2 +
        R_T * (delta_C_prime / S_C) * (delta_H_prime / S_H)
    )
    
    return float(delta_e)


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert RGB to hex color code"""
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex to RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def calculate_color_distance(rgb1: Tuple[int, int, int], 
                            rgb2: Tuple[int, int, int]) -> float:
    """
    Calculate perceptual color distance using Delta-E CIE2000
    
    Args:
        rgb1: First RGB color tuple (0-255)
        rgb2: Second RGB color tuple (0-255)
        
    Returns:
        Delta-E value (0-100+, lower is more similar)
    """
    lab1 = rgb_to_lab(rgb1)
    lab2 = rgb_to_lab(rgb2)
    return calculate_delta_e_2000(lab1, lab2)


def interpret_delta_e(delta_e: float) -> str:
    """Interpret Delta-E value for human understanding"""
    if delta_e < 1:
        return "Imperceptible difference"
    elif delta_e < 2:
        return "Just noticeable"
    elif delta_e < 5:
        return "Slight difference"
    elif delta_e < 10:
        return "Noticeable difference"
    elif delta_e < 20:
        return "Clear difference"
    elif delta_e < 40:
        return "Significant difference"
    elif delta_e < 60:
        return "Very different"
    else:
        return "Completely different"
