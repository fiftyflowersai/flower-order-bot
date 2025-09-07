import pandas as pd
import re

FILE_PATH = "data/BloombrainCatalogwithprices.xlsx"

def analyze_recommended_delivery_dates():
    """Analyze the Recommended Delivery Date column to find any extreme advance requirements"""
    
    df = pd.read_excel(FILE_PATH)
    
    print("RECOMMENDED DELIVERY DATE ANALYSIS")
    print("=" * 50)
    
    if 'attributes.Recommended Delivery Date' not in df.columns:
        print("Recommended Delivery Date column not found")
        return
    
    delivery_dates = df['attributes.Recommended Delivery Date'].dropna()
    unique_delivery_recs = delivery_dates.unique()
    
    print(f"Total products with delivery recommendations: {len(delivery_dates)}")
    print(f"Unique delivery recommendation patterns: {len(unique_delivery_recs)}")
    
    # Parse each recommendation to extract days in advance
    delivery_analysis = []
    
    for rec in unique_delivery_recs:
        rec_str = str(rec)
        product_count = (delivery_dates == rec).sum()
        
        # Extract days using regex
        days_match = re.search(r'(\d+)\s*days?\s*before', rec_str, re.IGNORECASE)
        weeks_match = re.search(r'(\d+)\s*weeks?\s*before', rec_str, re.IGNORECASE)
        
        days_advance = None
        
        if days_match:
            days_advance = int(days_match.group(1))
        elif weeks_match:
            days_advance = int(weeks_match.group(1)) * 7
        elif '2 to 3 days' in rec_str:
            days_advance = 2.5  # Average
        elif 'two weeks' in rec_str.lower():
            days_advance = 14
        
        delivery_analysis.append({
            'recommendation': rec_str,
            'days_advance': days_advance,
            'product_count': product_count
        })
    
    # Sort by days in advance
    delivery_analysis.sort(key=lambda x: x['days_advance'] if x['days_advance'] is not None else 0)
    
    print(f"\nDelivery recommendations by advance notice required:")
    print("=" * 70)
    
    total_with_days = 0
    max_days = 0
    
    for analysis in delivery_analysis:
        days = analysis['days_advance']
        count = analysis['product_count']
        rec = analysis['recommendation']
        
        if days is not None:
            total_with_days += count
            max_days = max(max_days, days)
            print(f"\n{days} days advance: {count} products")
        else:
            print(f"\nUnparseable: {count} products")
        
        # Show first 100 chars of recommendation
        print(f"  Text: {rec[:100]}...")
    
    print(f"\n" + "=" * 50)
    print("DELIVERY TIMING SUMMARY")
    print("=" * 50)
    
    print(f"Maximum advance notice required: {max_days} days")
    print(f"Products with parseable delivery timing: {total_with_days}")
    
    # Count products by delivery timing categories
    same_week = sum(a['product_count'] for a in delivery_analysis if a['days_advance'] and a['days_advance'] <= 7)
    two_weeks = sum(a['product_count'] for a in delivery_analysis if a['days_advance'] and 7 < a['days_advance'] <= 14)
    over_two_weeks = sum(a['product_count'] for a in delivery_analysis if a['days_advance'] and a['days_advance'] > 14)
    
    print(f"\nDelivery timing breakdown:")
    print(f"  ≤7 days advance: {same_week} products ({same_week/total_with_days*100:.1f}%)")
    print(f"  8-14 days advance: {two_weeks} products ({two_weeks/total_with_days*100:.1f}%)")
    print(f"  >14 days advance: {over_two_weeks} products ({over_two_weeks/total_with_days*100:.1f}%)")

def find_long_advance_products():
    """Find specific products that require long advance notice"""
    
    df = pd.read_excel(FILE_PATH)
    
    print(f"\n" + "=" * 50)
    print("PRODUCTS REQUIRING LONG ADVANCE NOTICE")
    print("=" * 50)
    
    if 'attributes.Recommended Delivery Date' not in df.columns:
        return
    
    # Look for products mentioning weeks or 10+ days
    long_advance_patterns = [
        'weeks',
        '10 days',
        '14 days',
        '15 days',
        '20 days',
        '30 days'
    ]
    
    long_advance_products = []
    
    for pattern in long_advance_patterns:
        matching_products = df[df['attributes.Recommended Delivery Date'].str.contains(pattern, case=False, na=False)]
        
        if len(matching_products) > 0:
            print(f"\nProducts mentioning '{pattern}': {len(matching_products)}")
            
            for _, product in matching_products.head(5).iterrows():
                long_advance_products.append({
                    'product_id': product.get('Product ID', 'N/A'),
                    'product_name': product.get('Product name', 'N/A'),
                    'group': product.get('Group', 'N/A'),
                    'delivery_rec': product.get('attributes.Recommended Delivery Date', 'N/A'),
                    'price': product.get('Variant price', 'N/A')
                })
    
    if long_advance_products:
        print(f"\nDetailed examples of long advance products:")
        print("-" * 70)
        
        for i, product in enumerate(long_advance_products[:10]):
            print(f"\nProduct {i+1}:")
            print(f"  ID: {product['product_id']}")
            print(f"  Name: {product['product_name']}")
            print(f"  Group: {product['group']}")
            print(f"  Price: ${product['price']}")
            print(f"  Delivery: {product['delivery_rec'][:100]}...")

def assess_delivery_impact_on_chatbot():
    """Assess whether delivery timing affects chatbot recommendation logic"""
    
    df = pd.read_excel(FILE_PATH)
    
    print(f"\n" + "=" * 50)
    print("CHATBOT IMPACT ASSESSMENT")
    print("=" * 50)
    
    if 'attributes.Recommended Delivery Date' not in df.columns:
        return
    
    delivery_dates = df['attributes.Recommended Delivery Date'].dropna()
    
    # Count products by realistic delivery categories
    standard_delivery = delivery_dates.str.contains('2 days|3 days|4 days', case=False, na=False).sum()
    extended_delivery = delivery_dates.str.contains('10 days|weeks|14 days', case=False, na=False).sum()
    
    total_with_delivery_info = len(delivery_dates)
    
    print(f"Products with delivery information: {total_with_delivery_info}")
    print(f"Standard delivery (2-4 days): {standard_delivery} ({standard_delivery/total_with_delivery_info*100:.1f}%)")
    print(f"Extended delivery (10+ days): {extended_delivery} ({extended_delivery/total_with_delivery_info*100:.1f}%)")
    
    print(f"\nCONCLUSION:")
    if extended_delivery / total_with_delivery_info < 0.05:  # Less than 5%
        print("✅ Your 1-week delivery assumption is valid")
        print("   <5% of products require extended delivery notice")
        print("   No need to add delivery timing logic to chatbot")
    else:
        print("⚠️  Consider delivery timing in recommendations")
        print(f"   {extended_delivery/total_with_delivery_info*100:.1f}% of products need >1 week advance")
        print("   May want to filter or note these for event recommendations")
    
    # Products without delivery information
    products_without_delivery = len(df) - len(delivery_dates)
    print(f"\nProducts without delivery recommendations: {products_without_delivery}")
    print(f"Assumption: These follow standard flower delivery timing (2-3 days)")

if __name__ == "__main__":
    analyze_recommended_delivery_dates()
    find_long_advance_products()
    assess_delivery_impact_on_chatbot()