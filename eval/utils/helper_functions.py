def prepare_item(row):
    return {
        'item_id': row['catlg_item_id'],
        'item_title': row['item_title'],
        'short_description': row['short_description'],
        'long_description': row['long_description'],
        'item_product_type': row['item_product_type'],
    }