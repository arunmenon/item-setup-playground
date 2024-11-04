import pandas as pd
import random

# Sample data components
brands = ['Nike', 'Adidas', 'Under Armour', 'Puma', 'Champion', 'Reebok', 'New Balance', 'Vans', 'ASICS', 'Levi\'s', 'Tommy Hilfiger', 'Calvin Klein', 'GAP', 'H&M', 'Uniqlo']
styles = ['Sport Performance', 'Classic Fit Crew Neck', 'Graphic Print', 'Slim Fit V-Neck', 'Retro Logo', 'Athletic Performance', 'Essentials Crew', 'Vintage Logo', 'Performance Training', 'Minimalist Crew', 'Vintage Pocket', 'Sustainable Organic', 'AIRism Ultra Light']
materials = ['cotton', 'polyester', 'blend', 'silk', 'wool', 'organic cotton', 'bamboo', 'linen']
features = ['moisture-wicking', 'breathable', 'flexible', 'quick-drying', 'soft fabric', 'durable stitching', 'reinforced seams', 'lightweight', 'eco-friendly']
apparel_styles = ['Crew Neck', 'V-Neck', 'Polo', 'Henley', 'Tank Top']
clothing_types = ['Tee', 'Shirt', 'Top', 'Polo Shirt', 'Crew Neck Tee']
counts_per_pack = [1, 2, 3, 4, 5]
size_groups = ['Women\'s', 'Men\'s', 'Unisex', 'Men\'s Big & Tall', 'Women\'s Plus']

# Generate 100 items
num_items = 100
data = []

for i in range(1, num_items + 1):
    brand = random.choice(brands)
    style = random.choice(styles)
    material = random.choice(materials)
    feature = random.choice(features)
    apparel_style = random.choice(apparel_styles)
    clothing_type = random.choice(clothing_types)
    count = random.choice(counts_per_pack)
    size_group = random.choice(size_groups)
    
    item_title = f"{brand} {style} {clothing_type}"
    short_description = f"{feature.capitalize()} {apparel_style.lower()} with {material} fabric."
    long_description = f"{brand} {style} {clothing_type} made from {material}, featuring {feature} properties, {apparel_style.lower()} design, and suitable for {size_group.lower()} sizes."
    item_product_type = "T-shirts"
    
    data.append({
        'item_title': item_title,
        'short_description': short_description,
        'long_description': long_description,
        'item_product_type': item_product_type
    })

# Create DataFrame
df = pd.DataFrame(data)

# Save to CSV
df.to_csv('input_items.csv', index=False)

print("Generated 'input_items.csv' with 100 items.")
