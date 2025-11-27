# Clothing Assets Directory

This directory contains PNG clothing images with transparent backgrounds for AR try-on.

## Structure

Each outfit type should have:
- Base PNG images (transparent background)
- Metadata in `metadata.json`

## Outfit Types

- `tshirt/` - T-shirt images
- `shirt/` - Shirt images  
- `kurta/` - Kurta images
- `dress/` - Dress images
- `hoodie/` - Hoodie images
- `jacket/` - Jacket images

## Image Requirements

- Format: PNG with transparent background
- Resolution: Minimum 512x512px
- Anchor points: Should align with shoulder, chest, waist positions
- Color: Will be dynamically colored based on user's skin tone matched colors

## Metadata Format

See `metadata.json` for anchor point definitions and scaling factors.

