"""
VastraVista Configuration Constants
"""

# Age groups
AGE_GROUPS = [
    {'name': 'Teen', 'range': '13-19', 'min': 13, 'max': 19},
    {'name': 'Young Adult', 'range': '20-35', 'min': 20, 'max': 35},
    {'name': 'Middle-aged', 'range': '35-55', 'min': 35, 'max': 55},
    {'name': 'Senior', 'range': '55+', 'min': 55, 'max': 100}
]

# Gender options
GENDER_OPTIONS = ['Male', 'Female']

# Skin undertones
SKIN_UNDERTONES = ['Warm', 'Cool', 'Neutral', 'Olive']

# Fashion color database (RGB values)
FASHION_COLORS = {
    # Neutrals & Basics
    'White': (255, 255, 255),
    'Ivory': (255, 255, 240),
    'Off White': (250, 250, 245),
    'Cream': (255, 253, 208),
    'Beige': (245, 245, 220),
    'Tan': (210, 180, 140),
    'Camel': (193, 154, 107),
    'Light Gray': (211, 211, 211),
    'Gray': (128, 128, 128),
    'Dark Gray': (80, 80, 80),
    'Charcoal': (54, 69, 79),
    'Black': (0, 0, 0),
    'Slate': (112, 128, 144),
    'Silver': (192, 192, 192),
    
    # Reds & Pinks
    'Red': (255, 0, 0),
    'Crimson': (220, 20, 60),
    'Scarlet': (255, 36, 0),
    'Ruby': (224, 17, 95),
    'Wine': (114, 47, 55),
    'Burgundy': (128, 0, 32),
    'Maroon': (128, 0, 0),
    'Cherry': (222, 49, 99),
    'Pink': (255, 192, 203),
    'Hot Pink': (255, 105, 180),
    'Fuchsia': (255, 0, 255),
    'Rose': (255, 0, 127),
    'Blush': (255, 224, 229),
    'Dusty Rose': (201, 145, 155),
    'Mauve': (224, 176, 255),
    
    # Oranges & Corals
    'Orange': (255, 165, 0),
    'Burnt Orange': (204, 85, 0),
    'Tangerine': (242, 133, 0),
    'Coral': (255, 127, 80),
    'Peach': (255, 218, 185),
    'Salmon': (250, 128, 114),
    'Rust': (183, 65, 14),
    'Terracotta': (226, 114, 91),
    'Apricot': (251, 206, 177),
    
    # Yellows & Golds
    'Yellow': (255, 255, 0),
    'Bright Yellow': (255, 253, 56),
    'Gold': (255, 215, 0),
    'Mustard': (255, 219, 88),
    'Golden Yellow': (255, 223, 0),
    'Lemon': (255, 247, 0),
    'Butter': (255, 240, 150),
    'Amber': (255, 191, 0),
    
    # Blues
    'Blue': (0, 0, 255),
    'Navy': (0, 0, 128),
    'Dark Navy': (0, 0, 90),
    'Royal Blue': (65, 105, 225),
    'Cobalt': (0, 71, 171),
    'Electric Blue': (125, 249, 255),
    'Sky Blue': (135, 206, 235),
    'Light Blue': (173, 216, 230),
    'Baby Blue': (137, 207, 240),
    'Powder Blue': (176, 224, 230),
    'Steel Blue': (70, 130, 180),
    'Denim Blue': (21, 96, 189),
    'Indigo': (75, 0, 130),
    'Midnight Blue': (25, 25, 112),
    'Periwinkle': (204, 204, 255),
    
    # Teals & Cyans
    'Teal': (0, 128, 128),
    'Turquoise': (64, 224, 208),
    'Cyan': (0, 255, 255),
    'Aqua': (127, 255, 212),
    'Aquamarine': (127, 255, 212),
    'Ice Blue': (175, 238, 238),
    'Ocean Blue': (0, 127, 159),
    'Seafoam': (147, 224, 210),
    
    # Greens
    'Green': (0, 128, 0),
    'Emerald': (80, 200, 120),
    'Kelly Green': (76, 187, 23),
    'Forest Green': (34, 139, 34),
    'Hunter Green': (53, 94, 59),
    'Dark Green': (1, 50, 32),
    'Olive': (128, 128, 0),
    'Olive Green': (107, 142, 35),
    'Sage': (188, 184, 138),
    'Mint': (189, 252, 201),
    'Lime': (191, 255, 0),
    'Chartreuse': (127, 255, 0),
    'Pine': (1, 121, 111),
    'Jade': (0, 168, 107),
    
    # Purples & Violets
    'Purple': (128, 0, 128),
    'Deep Purple': (102, 51, 153),
    'Violet': (138, 43, 226),
    'Lavender': (230, 230, 250),
    'Lilac': (200, 162, 200),
    'Magenta': (255, 0, 255),
    'Plum': (221, 160, 221),
    'Eggplant': (97, 64, 81),
    'Orchid': (218, 112, 214),
    'Amethyst': (153, 102, 204),
    'Grape': (111, 45, 168),
    
    # Browns & Earth Tones
    'Brown': (165, 42, 42),
    'Dark Brown': (101, 67, 33),
    'Chocolate': (210, 105, 30),
    'Coffee': (111, 78, 55),
    'Espresso': (74, 44, 42),
    'Taupe': (72, 60, 50),
    'Khaki': (240, 230, 140),
    'Earth Brown': (141, 94, 61),
    'Desert Sand': (237, 201, 175),
    'Clay': (185, 119, 78),
    'Moss': (138, 154, 91),
    'Cinnamon': (210, 105, 30),
    'Copper': (184, 115, 51),
    'Bronze': (205, 127, 50)
}

# Clothing categories by gender and age
CLOTHING_CATEGORIES = {
    'Male': {
        'Teen': {
            'casual': ['T-shirts', 'Hoodies', 'Jeans', 'Sneakers', 'Caps', 'Bomber Jackets'],
            'formal': ['Dress Shirts', 'Chinos', 'Blazers', 'Loafers'],
            'sports': ['Athletic Shorts', 'Sports Jersey', 'Running Shoes', 'Track Pants'],
            'party': ['Polo Shirts', 'Denim Jackets', 'Casual Blazers', 'Smart Sneakers']
        },
        'Young Adult': {
            'casual': ['Casual Shirts', 'Slim Jeans', 'Sneakers', 'T-shirts', 'Hoodies', 'Chinos'],
            'formal': ['Suits', 'Dress Shirts', 'Ties', 'Dress Shoes', 'Blazers', 'Formal Trousers'],
            'business': ['Business Suits', 'Oxford Shirts', 'Leather Shoes', 'Dress Pants'],
            'party': ['Fitted Shirts', 'Designer Jeans', 'Leather Jackets', 'Dress Boots'],
            'sports': ['Gym Wear', 'Athletic Shoes', 'Sports Jackets', 'Performance Wear']
        },
        'Middle-aged': {
            'casual': ['Polo Shirts', 'Khakis', 'Loafers', 'Casual Blazers', 'Dark Jeans'],
            'formal': ['Business Suits', 'Dress Shirts', 'Ties', 'Formal Shoes', 'Waistcoats'],
            'business': ['Executive Suits', 'Premium Shirts', 'Leather Briefcase', 'Cufflinks'],
            'smart_casual': ['Blazer + Jeans', 'Button-down Shirts', 'Chelsea Boots'],
            'weekend': ['Casual Jackets', 'Comfortable Pants', 'Casual Shoes']
        },
        'Senior': {
            'casual': ['Comfortable Shirts', 'Easy-fit Pants', 'Comfortable Shoes', 'Cardigans'],
            'formal': ['Classic Suits', 'Dress Shirts', 'Comfortable Formal Shoes', 'Ties'],
            'smart_casual': ['Sport Coats', 'Dress Pants', 'Comfortable Loafers'],
            'relaxed': ['Polo Shirts', 'Khakis', 'Slip-on Shoes', 'Vests']
        }
    },
    'Female': {
        'Teen': {
            'casual': ['T-shirts', 'Jeans', 'Sneakers', 'Hoodies', 'Crop Tops', 'Denim Jackets'],
            'formal': ['Dresses', 'Skirts', 'Blouses', 'Flats', 'Formal Pants'],
            'party': ['Party Dresses', 'Heels', 'Stylish Tops', 'Accessories'],
            'sports': ['Athletic Wear', 'Leggings', 'Sports Bras', 'Running Shoes']
        },
        'Young Adult': {
            'casual': ['Tops', 'Jeans', 'Dresses', 'Sneakers', 'Casual Jackets'],
            'formal': ['Business Suits', 'Blazers', 'Dress Pants', 'Pumps', 'Formal Dresses'],
            'business': ['Pantsuits', 'Pencil Skirts', 'Blouses', 'Professional Heels'],
            'party': ['Cocktail Dresses', 'Evening Wear', 'High Heels', 'Clutches'],
            'ethnic': ['Sarees', 'Kurtas', 'Salwar Kameez', 'Ethnic Jewelry'],
            'western': ['Dresses', 'Jumpsuits', 'Rompers', 'Midi Skirts']
        },
        'Middle-aged': {
            'casual': ['Comfortable Tops', 'Classic Jeans', 'Flats', 'Cardigans'],
            'formal': ['Business Dresses', 'Blazers', 'Dress Pants', 'Classic Pumps'],
            'business': ['Professional Suits', 'Silk Blouses', 'Elegant Shoes'],
            'elegant': ['A-line Dresses', 'Wrap Dresses', 'Classic Jewelry'],
            'ethnic': ['Designer Sarees', 'Elegant Kurtas', 'Traditional Jewelry']
        },
        'Senior': {
            'casual': ['Comfortable Tops', 'Easy-fit Pants', 'Comfortable Shoes', 'Light Jackets'],
            'formal': ['Classic Dresses', 'Comfortable Suits', 'Low Heels', 'Elegant Accessories'],
            'ethnic': ['Comfortable Sarees', 'Cotton Kurtas', 'Traditional Wear'],
            'elegant': ['Timeless Pieces', 'Classic Cuts', 'Comfortable Footwear']
        }
    }
}

# Delta-E thresholds
DELTA_E_THRESHOLDS = {
    'imperceptible': 1.0,
    'just_noticeable': 2.0,
    'noticeable': 10.0,
    'excellent_min': 15.0,
    'excellent_max': 40.0,
    'good_max': 60.0
}

# Model paths
MODEL_PATHS = {
    'face_detection': 'ml/saved_models/face_detector.xml',
    'age_model': 'ml/saved_models/age_model.pt',
    'gender_model': 'ml/saved_models/gender_model.pt'
}

# Image processing
MAX_IMAGE_SIZE = (1920, 1080)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
