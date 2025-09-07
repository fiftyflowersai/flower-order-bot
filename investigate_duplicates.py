import pandas as pd

FILE_PATH = "data/BloombrainCatalogwithprices.xlsx"

def find_delivery_option_examples():
    """Find specific examples of products with delivery-related options"""
    
    df = pd.read_excel(FILE_PATH)
    
    # Create composite ID and find duplicates
    df['composite_id'] = df['Product ID'].astype(str) + '_' + df['Variant ID'].astype(str)
    duplicated_ids = df[df['composite_id'].duplicated(keep=False)]
    
    print("DELIVERY OPTION EXAMPLES")
    print("=" * 50)
    
    # Delivery keywords
    delivery_keywords = ['delivery', 'rush', 'shipping', 'expedited', 'express', 'fee', 'upgrade']
    
    # Get unique composite IDs
    unique_composite_ids = duplicated_ids['composite_id'].unique()
    
    delivery_examples = []
    
    for composite_id in unique_composite_ids:
        rows = duplicated_ids[duplicated_ids['composite_id'] == composite_id]
        option_labels = rows['Option value label'].dropna().unique()
        
        # Check if any options are delivery-related
        delivery_options = []
        for label in option_labels:
            label_lower = str(label).lower()
            if any(kw in label_lower for kw in delivery_keywords):
                delivery_options.append(label)
        
        if delivery_options:
            delivery_examples.append({
                'product_id': rows['Product ID'].iloc[0],
                'variant_id': rows['Variant ID'].iloc[0],
                'composite_id': composite_id,
                'product_name': rows['Product name'].iloc[0],
                'num_variations': len(rows),
                'all_options': list(option_labels),
                'delivery_options': delivery_options,
                'colors_field': rows['Colors (by semicolon)'].iloc[0],
                'price': rows['Variant price'].iloc[0]
            })
    
    print(f"Found {len(delivery_examples)} products with delivery-related options")
    
    print(f"\nDELIVERY OPTION EXAMPLES FOR MANUAL INSPECTION:")
    print("=" * 60)
    
    for i, example in enumerate(delivery_examples[:15]):
        print(f"\nExample {i+1} - FOR WEBSITE/EXCEL LOOKUP:")
        print(f"  Product ID: {example['product_id']}")
        print(f"  Variant ID: {example['variant_id']}")
        print(f"  Product Name: {example['product_name']}")
        print(f"  Price: ${example['price']}")
        print(f"  Colors Field: {example['colors_field']}")
        print(f"  Number of option variations: {example['num_variations']}")
        print(f"  Delivery options found: {example['delivery_options']}")
        print(f"  All options: {example['all_options']}")
    
    # Show detailed breakdown of delivery option types
    print(f"\n" + "=" * 60)
    print("DELIVERY OPTION TYPE BREAKDOWN")
    print("=" * 60)
    
    all_delivery_options = []
    for example in delivery_examples:
        all_delivery_options.extend(example['delivery_options'])
    
    unique_delivery_options = list(set(all_delivery_options))
    print(f"Unique delivery options found: {len(unique_delivery_options)}")
    
    for option in unique_delivery_options:
        print(f"  {option}")

def show_specific_delivery_product_details():
    """Show detailed breakdown of a specific delivery product for analysis"""
    
    df = pd.read_excel(FILE_PATH)
    
    # Create composite ID and find duplicates
    df['composite_id'] = df['Product ID'].astype(str) + '_' + df['Variant ID'].astype(str)
    duplicated_ids = df[df['composite_id'].duplicated(keep=False)]
    
    # Find first delivery example
    delivery_keywords = ['delivery', 'rush', 'shipping', 'expedited', 'express', 'fee']
    
    for composite_id in duplicated_ids['composite_id'].unique():
        rows = duplicated_ids[duplicated_ids['composite_id'] == composite_id]
        option_labels = rows['Option value label'].dropna().unique()
        
        has_delivery = any(any(kw in str(label).lower() for kw in delivery_keywords) for label in option_labels)
        
        if has_delivery:
            print(f"\n" + "=" * 60)
            print(f"DETAILED DELIVERY EXAMPLE: {composite_id}")
            print("=" * 60)
            
            print(f"Product: {rows['Product name'].iloc[0]}")
            print(f"Number of rows: {len(rows)}")
            
            # Show each row's details
            display_cols = ['Product ID', 'Variant ID', 'Product name', 'Variant price', 'Option value label', 'Option value price']
            available_cols = [col for col in display_cols if col in rows.columns]
            
            for i, (_, row) in enumerate(rows.iterrows()):
                print(f"\nRow {i+1}:")
                for col in available_cols:
                    print(f"  {col}: {row[col]}")
            
            break  # Just show first example

if __name__ == "__main__":
    find_delivery_option_examples()
    show_specific_delivery_product_details()