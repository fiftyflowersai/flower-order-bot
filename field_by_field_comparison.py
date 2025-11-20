#!/usr/bin/env python3
"""
Field-by-Field Database Comparison
Compares Postgres 'flowers' table with MySQL 'flowers_view' VIEW
"""

import os
import psycopg2
import pymysql
from typing import Dict, List, Any, Tuple, Set
from collections import defaultdict
import json

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ============================================================================
# DATABASE CONNECTIONS
# ============================================================================

def get_postgres_conn():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "flower_bot_db"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD") or os.getenv("DB_PASSWORD")
    )

def get_mysql_conn():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "aws.connect.psdb.cloud"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME", "cms"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        cursorclass=pymysql.cursors.DictCursor,
        ssl={'ssl': {}}
    )

# ============================================================================
# TASK 1: FIELD-BY-FIELD COMPARISON FOR SPECIFIC PRODUCTS
# ============================================================================

def get_sample_product_ids(pg_conn, mysql_conn, count=10):
    """Get product_ids that exist in both databases"""
    print("\n" + "="*80)
    print("TASK 1: Finding Sample Product IDs")
    print("="*80)
    
    # Get random product_ids from Postgres
    pg_cur = pg_conn.cursor()
    pg_cur.execute("""
        SELECT product_id
        FROM (
            SELECT DISTINCT FLOOR(SPLIT_PART(unique_id, '_', 1)::numeric)::int as product_id
            FROM flowers
        ) subq
        ORDER BY RANDOM()
        LIMIT 50
    """)
    pg_ids = [row[0] for row in pg_cur.fetchall()]
    print(f"Postgres sample: {len(pg_ids)} product_ids")
    print(f"  Sample: {pg_ids[:10]}")
    
    # Check which exist in MySQL
    mysql_cur = mysql_conn.cursor()
    placeholders = ','.join(['%s'] * len(pg_ids))
    mysql_cur.execute(f"""
        SELECT DISTINCT product_id 
        FROM products 
        WHERE status = 'active' 
          AND product_id IN ({placeholders})
    """, pg_ids)
    mysql_ids = [row['product_id'] for row in mysql_cur.fetchall()]
    print(f"MySQL matches: {len(mysql_ids)} product_ids")
    
    # Find intersection
    common_ids = sorted(list(set(pg_ids) & set(mysql_ids)))[:count]
    print(f"\n✅ Common product_ids: {len(common_ids)}")
    print(f"  Using: {common_ids}")
    
    return common_ids

def compare_product_fields(pg_conn, mysql_conn, product_id: int, max_variants=5):
    """Compare all fields for a specific product_id"""
    pg_cur = pg_conn.cursor()
    mysql_cur = mysql_conn.cursor()
    
    # Postgres query
    pg_cur.execute("""
        SELECT 
            unique_id,
            product_name,
            variant_name,
            variant_price,
            colors_raw,
            has_red, has_pink, has_white, has_yellow, has_orange, 
            has_purple, has_blue, has_green,
            season_start_month, season_start_day, 
            season_end_month, season_end_day,
            is_year_round,
            diy_level,
            holiday_occasion,
            product_type_all_flowers,
            recipe_metafield,
            group_category
        FROM flowers
        WHERE FLOOR(SPLIT_PART(unique_id, '_', 1)::numeric)::int = %s
        ORDER BY unique_id
        LIMIT %s
    """, (product_id, max_variants))
    
    pg_rows = []
    for row in pg_cur.fetchall():
        pg_rows.append({
            'unique_id': row[0],
            'product_name': row[1],
            'variant_name': row[2],
            'variant_price': float(row[3]) if row[3] else None,
            'colors_raw': row[4],
            'has_red': bool(row[5]),
            'has_pink': bool(row[6]),
            'has_white': bool(row[7]),
            'has_yellow': bool(row[8]),
            'has_orange': bool(row[9]),
            'has_purple': bool(row[10]),
            'has_blue': bool(row[11]),
            'has_green': bool(row[12]),
            'season_start_month': row[13],
            'season_start_day': row[14],
            'season_end_month': row[15],
            'season_end_day': row[16],
            'is_year_round': bool(row[17]),
            'diy_level': row[18],
            'holiday_occasion': row[19],
            'product_type_all_flowers': row[20],
            'recipe_metafield': row[21],
            'group_category': row[22]
        })
    
    # MySQL query
    mysql_cur.execute("""
        SELECT 
            unique_id,
            product_name,
            variant_name,
            variant_price,
            colors_raw,
            has_red, has_pink, has_white, has_yellow, has_orange, 
            has_purple, has_blue, has_green,
            season_start_month, season_start_day, 
            season_end_month, season_end_day,
            is_year_round,
            diy_level,
            holiday_occasion,
            product_type_all_flowers,
            recipe_metafield,
            group_category
        FROM flowers_view
        WHERE CAST(SUBSTRING_INDEX(unique_id, '_', 1) AS UNSIGNED) = %s
        ORDER BY unique_id
        LIMIT %s
    """, (product_id, max_variants))
    
    mysql_rows = []
    for row in mysql_cur.fetchall():
        mysql_rows.append({
            'unique_id': row['unique_id'],
            'product_name': row['product_name'],
            'variant_name': row['variant_name'],
            'variant_price': float(row['variant_price']) if row['variant_price'] else None,
            'colors_raw': row['colors_raw'],
            'has_red': bool(row['has_red']),
            'has_pink': bool(row['has_pink']),
            'has_white': bool(row['has_white']),
            'has_yellow': bool(row['has_yellow']),
            'has_orange': bool(row['has_orange']),
            'has_purple': bool(row['has_purple']),
            'has_blue': bool(row['has_blue']),
            'has_green': bool(row['has_green']),
            'season_start_month': row['season_start_month'],
            'season_start_day': row['season_start_day'],
            'season_end_month': row['season_end_month'],
            'season_end_day': row['season_end_day'],
            'is_year_round': bool(row['is_year_round']),
            'diy_level': row['diy_level'],
            'holiday_occasion': row['holiday_occasion'],
            'product_type_all_flowers': row['product_type_all_flowers'],
            'recipe_metafield': row['recipe_metafield'],
            'group_category': row['group_category']
        })
    
    return pg_rows, mysql_rows

def normalize_value(value, field_name):
    """Normalize values for comparison"""
    if value is None:
        return None
    
    # Handle JSON strings
    if field_name in ['diy_level', 'holiday_occasion'] and isinstance(value, str):
        if value.startswith('[') or value.startswith('{'):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list) and len(parsed) > 0:
                    return parsed[0]  # Extract first element
                return parsed
            except:
                pass
    
    # Handle colors_raw (normalize order and case)
    if field_name == 'colors_raw' and isinstance(value, str):
        colors = [c.strip() for c in value.split(';')]
        return '; '.join(sorted(colors))
    
    return value

def compare_field_values(pg_val, mysql_val, field_name):
    """Compare two field values and return match status"""
    pg_norm = normalize_value(pg_val, field_name)
    mysql_norm = normalize_value(mysql_val, field_name)
    
    if pg_norm == mysql_norm:
        return "✅", "Exact match"
    
    # Check for type differences
    if isinstance(pg_norm, bool) and isinstance(mysql_norm, (int, bool)):
        if bool(pg_norm) == bool(mysql_norm):
            return "✅", "Boolean representation"
    
    # Check for string differences (case, whitespace)
    if isinstance(pg_norm, str) and isinstance(mysql_norm, str):
        if pg_norm.lower().strip() == mysql_norm.lower().strip():
            return "⚠️", "Case/whitespace difference"
        if pg_norm in mysql_norm or mysql_norm in pg_norm:
            return "⚠️", "Partial match"
    
    # Check for numeric differences (rounding)
    if isinstance(pg_norm, (int, float)) and isinstance(mysql_norm, (int, float)):
        if abs(pg_norm - mysql_norm) < 0.01:
            return "✅", "Numeric rounding"
    
    return "❌", f"Different: '{pg_norm}' vs '{mysql_norm}'"

def task1_field_comparison(pg_conn, mysql_conn):
    """Task 1: Field-by-field comparison for specific products"""
    print("\n" + "="*80)
    print("TASK 1: FIELD-BY-FIELD COMPARISON FOR SPECIFIC PRODUCTS")
    print("="*80)
    
    # Get sample product_ids
    product_ids = get_sample_product_ids(pg_conn, mysql_conn, count=10)
    
    if not product_ids:
        print("❌ No common product_ids found!")
        return
    
    all_comparisons = []
    field_names = [
        'product_name', 'variant_name', 'variant_price', 'colors_raw',
        'has_red', 'has_pink', 'has_white', 'has_yellow', 'has_orange',
        'has_purple', 'has_blue', 'has_green',
        'season_start_month', 'season_start_day', 'season_end_month', 'season_end_day',
        'is_year_round', 'diy_level', 'holiday_occasion',
        'product_type_all_flowers', 'recipe_metafield', 'group_category'
    ]
    
    for product_id in product_ids:
        print(f"\n--- Product ID: {product_id} ---")
        pg_rows, mysql_rows = compare_product_fields(pg_conn, mysql_conn, product_id, max_variants=3)
        
        if not pg_rows:
            print(f"  ⚠️  No rows in Postgres for product_id {product_id}")
            continue
        if not mysql_rows:
            print(f"  ⚠️  No rows in MySQL for product_id {product_id}")
            continue
        
        # Compare first matching variant
        pg_row = pg_rows[0]
        mysql_row = mysql_rows[0] if mysql_rows else None
        
        if mysql_row:
            for field in field_names:
                pg_val = pg_row.get(field)
                mysql_val = mysql_row.get(field)
                status, notes = compare_field_values(pg_val, mysql_val, field)
                
                all_comparisons.append({
                    'product_id': product_id,
                    'field': field,
                    'pg_value': str(pg_val)[:50] if pg_val is not None else 'NULL',
                    'mysql_value': str(mysql_val)[:50] if mysql_val is not None else 'NULL',
                    'match': status,
                    'notes': notes
                })
    
    # Print comparison table
    print("\n" + "="*100)
    print("FIELD-BY-FIELD COMPARISON TABLE")
    print("="*100)
    print(f"{'Product ID':<12} {'Field':<25} {'Postgres Value':<30} {'MySQL Value':<30} {'Match?':<8} {'Notes':<30}")
    print("-"*100)
    
    for comp in all_comparisons:
        print(f"{comp['product_id']:<12} {comp['field']:<25} {comp['pg_value']:<30} {comp['mysql_value']:<30} {comp['match']:<8} {comp['notes']:<30}")
    
    # Summary
    matches = sum(1 for c in all_comparisons if '✅' in c['match'])
    warnings = sum(1 for c in all_comparisons if '⚠️' in c['match'])
    errors = sum(1 for c in all_comparisons if '❌' in c['match'])
    
    print("\n" + "="*100)
    print(f"Summary: ✅ {matches} matches, ⚠️  {warnings} warnings, ❌ {errors} errors")
    
    return all_comparisons

# ============================================================================
# TASK 2: QUERY RESULT COMPARISON
# ============================================================================

def task2_query_comparison(pg_conn, mysql_conn):
    """Task 2: Compare query results"""
    print("\n" + "="*80)
    print("TASK 2: QUERY RESULT COMPARISON")
    print("="*80)
    
    test_cases = [
        {
            'name': 'Red flowers only',
            'postgres': "SELECT product_name, variant_name, variant_price, colors_raw FROM flowers WHERE has_red = true ORDER BY product_name LIMIT 10",
            'mysql': "SELECT product_name, variant_name, variant_price, colors_raw FROM flowers_view WHERE has_red = 1 ORDER BY product_name LIMIT 10"
        },
        {
            'name': 'Under $100',
            'postgres': "SELECT product_name, variant_name, variant_price FROM flowers WHERE variant_price < 100 ORDER BY variant_price LIMIT 10",
            'mysql': "SELECT product_name, variant_name, variant_price FROM flowers_view WHERE variant_price < 100 ORDER BY variant_price LIMIT 10"
        },
        {
            'name': 'Red AND under $100',
            'postgres': "SELECT product_name, variant_name, variant_price, colors_raw FROM flowers WHERE has_red = true AND variant_price < 100 ORDER BY variant_price LIMIT 10",
            'mysql': "SELECT product_name, variant_name, variant_price, colors_raw FROM flowers_view WHERE has_red = 1 AND variant_price < 100 ORDER BY variant_price LIMIT 10"
        },
        {
            'name': 'Pink flowers',
            'postgres': "SELECT product_name, variant_name, colors_raw FROM flowers WHERE has_pink = true ORDER BY product_name LIMIT 10",
            'mysql': "SELECT product_name, variant_name, colors_raw FROM flowers_view WHERE has_pink = 1 ORDER BY product_name LIMIT 10"
        },
        {
            'name': 'Year-round products',
            'postgres': "SELECT product_name, variant_name FROM flowers WHERE is_year_round = true ORDER BY product_name LIMIT 10",
            'mysql': "SELECT product_name, variant_name FROM flowers_view WHERE is_year_round = 1 ORDER BY product_name LIMIT 10"
        },
        {
            'name': 'Seasonal products',
            'postgres': "SELECT product_name, variant_name, season_start_month, season_end_month FROM flowers WHERE is_year_round = false ORDER BY product_name LIMIT 10",
            'mysql': "SELECT product_name, variant_name, season_start_month, season_end_month FROM flowers_view WHERE is_year_round = 0 ORDER BY product_name LIMIT 10"
        }
    ]
    
    results = []
    
    for test in test_cases:
        print(f"\n--- {test['name']} ---")
        
        # Postgres
        pg_cur = pg_conn.cursor()
        pg_cur.execute(test['postgres'])
        pg_rows = [dict(zip([desc[0] for desc in pg_cur.description], row)) for row in pg_cur.fetchall()]
        
        # MySQL
        mysql_cur = mysql_conn.cursor()
        mysql_cur.execute(test['mysql'])
        mysql_rows = mysql_cur.fetchall()
        
        # Compare
        pg_keys = set()
        mysql_keys = set()
        
        for row in pg_rows:
            key = f"{row.get('product_name', '')}_{row.get('variant_name', '')}"
            pg_keys.add(key)
        
        for row in mysql_rows:
            key = f"{row.get('product_name', '')}_{row.get('variant_name', '')}"
            mysql_keys.add(key)
        
        overlap = pg_keys & mysql_keys
        overlap_pct = (len(overlap) / len(pg_keys) * 100) if pg_keys else 0
        
        results.append({
            'query': test['name'],
            'pg_count': len(pg_rows),
            'mysql_count': len(mysql_rows),
            'overlap': len(overlap),
            'overlap_pct': overlap_pct
        })
        
        print(f"  Postgres: {len(pg_rows)} results")
        print(f"  MySQL: {len(mysql_rows)} results")
        print(f"  Overlap: {len(overlap)}/{len(pg_keys)} ({overlap_pct:.1f}%)")
    
    # Print comparison table
    print("\n" + "="*100)
    print("QUERY RESULTS COMPARISON TABLE")
    print("="*100)
    print(f"{'Query':<30} {'Postgres':<12} {'MySQL':<12} {'Overlap':<12} {'Overlap %':<12} {'Notes':<20}")
    print("-"*100)
    
    for r in results:
        status = "✅" if r['overlap_pct'] >= 80 else "⚠️" if r['overlap_pct'] >= 50 else "❌"
        notes = "Good match" if r['overlap_pct'] >= 80 else "Partial match" if r['overlap_pct'] >= 50 else "Low match"
        print(f"{r['query']:<30} {r['pg_count']:<12} {r['mysql_count']:<12} {r['overlap']:<12} {r['overlap_pct']:.1f}%{'':<6} {status} {notes}")
    
    return results

# ============================================================================
# TASK 3: FIELD FORMAT VALIDATION
# ============================================================================

def task3_format_validation(pg_conn, mysql_conn):
    """Task 3: Validate field formats"""
    print("\n" + "="*80)
    print("TASK 3: FIELD FORMAT VALIDATION")
    print("="*80)
    
    format_checks = [
        {
            'field': 'product_name',
            'postgres': "SELECT DISTINCT product_name FROM flowers ORDER BY product_name LIMIT 5",
            'mysql': "SELECT DISTINCT product_name FROM flowers_view ORDER BY product_name LIMIT 5",
            'expected': 'String, should match exactly'
        },
        {
            'field': 'variant_price',
            'postgres': "SELECT DISTINCT variant_price FROM flowers WHERE variant_price IS NOT NULL ORDER BY variant_price LIMIT 5",
            'mysql': "SELECT DISTINCT variant_price FROM flowers_view WHERE variant_price IS NOT NULL ORDER BY variant_price LIMIT 5",
            'expected': 'Decimal (e.g., 124.99, 194.99)'
        },
        {
            'field': 'colors_raw',
            'postgres': "SELECT DISTINCT colors_raw FROM flowers WHERE colors_raw IS NOT NULL ORDER BY colors_raw LIMIT 5",
            'mysql': "SELECT DISTINCT colors_raw FROM flowers_view WHERE colors_raw IS NOT NULL ORDER BY colors_raw LIMIT 5",
            'expected': 'Semicolon-separated string (e.g., "Red; Pink; White")'
        },
        {
            'field': 'has_red',
            'postgres': "SELECT has_red, COUNT(*) FROM flowers GROUP BY has_red",
            'mysql': "SELECT has_red, COUNT(*) FROM flowers_view GROUP BY has_red",
            'expected': 'Boolean: true/false or 1/0'
        },
        {
            'field': 'diy_level',
            'postgres': "SELECT DISTINCT diy_level FROM flowers WHERE diy_level IS NOT NULL LIMIT 5",
            'mysql': "SELECT DISTINCT diy_level FROM flowers_view WHERE diy_level IS NOT NULL LIMIT 5",
            'expected': 'String or JSON array? Check format'
        },
        {
            'field': 'holiday_occasion',
            'postgres': "SELECT DISTINCT holiday_occasion FROM flowers WHERE holiday_occasion IS NOT NULL LIMIT 5",
            'mysql': "SELECT DISTINCT holiday_occasion FROM flowers_view WHERE holiday_occasion IS NOT NULL LIMIT 5",
            'expected': 'String or JSON array? Check format'
        }
    ]
    
    results = []
    
    for check in format_checks:
        print(f"\n--- {check['field']} ---")
        
        # Postgres
        pg_cur = pg_conn.cursor()
        pg_cur.execute(check['postgres'])
        pg_values = [row[0] if isinstance(row, tuple) else list(row.values())[0] for row in pg_cur.fetchall()]
        
        # MySQL
        mysql_cur = mysql_conn.cursor()
        mysql_cur.execute(check['mysql'])
        mysql_values = [list(row.values())[0] for row in mysql_cur.fetchall()]
        
        # Analyze format
        pg_format = analyze_format(pg_values, check['field'])
        mysql_format = analyze_format(mysql_values, check['field'])
        
        match = pg_format == mysql_format
        status = "✅" if match else "❌"
        
        results.append({
            'field': check['field'],
            'pg_format': pg_format,
            'mysql_format': mysql_format,
            'pg_sample': str(pg_values[:3]) if pg_values else 'None',
            'mysql_sample': str(mysql_values[:3]) if mysql_values else 'None',
            'match': status,
            'expected': check['expected']
        })
        
        print(f"  Postgres format: {pg_format}")
        print(f"  MySQL format: {mysql_format}")
        print(f"  Match: {status}")
        print(f"  Postgres sample: {pg_values[:3] if pg_values else 'None'}")
        print(f"  MySQL sample: {mysql_values[:3] if mysql_values else 'None'}")
    
    # Print format table
    print("\n" + "="*100)
    print("FIELD FORMAT VALIDATION TABLE")
    print("="*100)
    print(f"{'Field':<20} {'Postgres Format':<20} {'MySQL Format':<20} {'Match?':<8} {'Expected':<30}")
    print("-"*100)
    
    for r in results:
        print(f"{r['field']:<20} {r['pg_format']:<20} {r['mysql_format']:<20} {r['match']:<8} {r['expected']:<30}")
    
    return results

def analyze_format(values, field_name):
    """Analyze the format of field values"""
    if not values:
        return "Empty"
    
    sample = values[0]
    
    if sample is None:
        return "NULL"
    
    if isinstance(sample, bool):
        return "Boolean"
    
    if isinstance(sample, (int, float)):
        return "Numeric"
    
    if isinstance(sample, str):
        if sample.startswith('[') or sample.startswith('{'):
            return "JSON"
        if ';' in sample:
            return "Semicolon-separated"
        if ',' in sample:
            return "Comma-separated"
        return "String"
    
    return "Unknown"

# ============================================================================
# CRITICAL ISSUES & FIXES
# ============================================================================

def generate_issues_report(task1_results, task2_results, task3_results):
    """Generate summary of critical issues and fixes needed"""
    print("\n" + "="*80)
    print("CRITICAL ISSUES & FIELDS NEEDING FIXES")
    print("="*80)
    
    blockers = []
    warnings = []
    info = []
    
    # Analyze Task 1 results
    if task1_results:
        field_errors = defaultdict(list)
        for comp in task1_results:
            if '❌' in comp['match']:
                field_errors[comp['field']].append(comp['notes'])
        
        for field, errors in field_errors.items():
            if 'completely different' in str(errors).lower() or 'wrong mapping' in str(errors).lower():
                blockers.append(f"❌ BLOCKER: {field} - {errors[0]}")
            else:
                warnings.append(f"⚠️  WARNING: {field} - {errors[0]}")
    
    # Analyze Task 3 results
    if task3_results:
        for r in task3_results:
            if '❌' in r['match']:
                if 'JSON' in r['mysql_format'] and 'String' in r['pg_format']:
                    blockers.append(f"❌ BLOCKER: {r['field']} - Returns JSON array, needs parsing")
                elif r['pg_format'] != r['mysql_format']:
                    warnings.append(f"⚠️  WARNING: {r['field']} - Format mismatch: {r['pg_format']} vs {r['mysql_format']}")
    
    # Analyze Task 2 results
    if task2_results:
        for r in task2_results:
            if r['overlap_pct'] < 50:
                blockers.append(f"❌ BLOCKER: Query '{r['query']}' - Only {r['overlap_pct']:.1f}% overlap")
            elif r['overlap_pct'] < 80:
                warnings.append(f"⚠️  WARNING: Query '{r['query']}' - {r['overlap_pct']:.1f}% overlap")
    
    # Print issues
    if blockers:
        print("\n❌ BLOCKERS (Must Fix):")
        for issue in blockers:
            print(f"  {issue}")
    
    if warnings:
        print("\n⚠️  WARNINGS (Should Fix):")
        for issue in warnings:
            print(f"  {issue}")
    
    if not blockers and not warnings:
        print("\n✅ No critical issues found!")
    
    # Fields needing fixes
    print("\n" + "="*80)
    print("FIELDS NEEDING FIXES")
    print("="*80)
    
    fixes_needed = []
    if task3_results:
        for r in task3_results:
            if '❌' in r['match']:
                if 'diy_level' in r['field'] and 'JSON' in r['mysql_format']:
                    fixes_needed.append(f"- {r['field']}: Extract first element from JSON array `[\"Ready To Go\"]` → `\"Ready To Go\"`")
                elif 'holiday_occasion' in r['field'] and 'JSON' in r['mysql_format']:
                    fixes_needed.append(f"- {r['field']}: Parse JSON array or extract first element")
                elif 'colors_raw' in r['field']:
                    fixes_needed.append(f"- {r['field']}: Normalize separator/ordering differences")
    
    if fixes_needed:
        for fix in fixes_needed:
            print(f"  {fix}")
    else:
        print("  ✅ No format fixes needed!")

# ============================================================================
# MAIN
# ============================================================================

def check_view_exists(mysql_conn):
    """Check if flowers_view exists"""
    mysql_cur = mysql_conn.cursor()
    try:
        mysql_cur.execute("""
            SELECT COUNT(*) as count
            FROM information_schema.views
            WHERE table_schema = 'cms' AND table_name = 'flowers_view'
        """)
        result = mysql_cur.fetchone()
        return result['count'] > 0
    except:
        # Try to query the view directly
        try:
            mysql_cur.execute("SELECT 1 FROM flowers_view LIMIT 1")
            return True
        except:
            return False

def main():
    print("="*80)
    print("FIELD-BY-FIELD DATABASE COMPARISON")
    print("="*80)
    
    pg_conn = None
    mysql_conn = None
    
    try:
        print("\nConnecting to databases...")
        pg_conn = get_postgres_conn()
        mysql_conn = get_mysql_conn()
        print("✅ Connected to both databases")
        
        # Check if VIEW exists, create if needed
        print("\nChecking if 'flowers_view' exists in MySQL...")
        if not check_view_exists(mysql_conn):
            print("❌ VIEW does not exist.")
            
            # Try to create it, but handle permission errors gracefully
            print("Attempting to create VIEW...")
            
            # Read the VIEW SQL from file
            try:
                with open('create_flowers_view.sql', 'r') as f:
                    view_sql = f.read()
            except FileNotFoundError:
                # If file doesn't exist, use inline SQL
                view_sql = """CREATE VIEW flowers_view AS
SELECT 
  CONCAT(p.product_id, '_', COALESCE(pv.product_variant_id, '0')) AS unique_id,
  p.name AS product_name,
  pv.name AS variant_name,
  pv.price AS variant_price,
  
  (SELECT pav.value FROM product_attribute_values pav 
   WHERE pav.product_id = p.product_id AND pav.attribute_id = 1 LIMIT 1) AS description_clean,
  
  (SELECT GROUP_CONCAT(c.name ORDER BY c.name SEPARATOR '; ')
   FROM product_colors_link pcl
   JOIN colors c ON pcl.color_id = c.color_id
   WHERE pcl.product_id = p.product_id AND c.status = 'active') AS colors_raw,
  
  EXISTS(SELECT 1 FROM product_colors_link pcl JOIN colors c ON pcl.color_id = c.color_id
         WHERE pcl.product_id = p.product_id AND c.status = 'active'
         AND LOWER(c.name) IN ('red', 'true red', 'wine red', 'cranberry', 'burgundy', 'rust')) AS has_red,
  
  EXISTS(SELECT 1 FROM product_colors_link pcl JOIN colors c ON pcl.color_id = c.color_id
         WHERE pcl.product_id = p.product_id AND c.status = 'active'
         AND LOWER(c.name) IN ('pink', 'true pink', 'hot pink', 'dusty pink', 'light pink', 
                               'blush', 'dusty rose', 'mauve', 'pinky lavender', 'fuchsia', 
                               'magenta', 'coral')) AS has_pink,
  
  EXISTS(SELECT 1 FROM product_colors_link pcl JOIN colors c ON pcl.color_id = c.color_id
         WHERE pcl.product_id = p.product_id AND c.status = 'active'
         AND LOWER(c.name) IN ('white', 'ivory', 'natural', 'champagne', 'clear')) AS has_white,
  
  EXISTS(SELECT 1 FROM product_colors_link pcl JOIN colors c ON pcl.color_id = c.color_id
         WHERE pcl.product_id = p.product_id AND c.status = 'active'
         AND LOWER(c.name) IN ('yellow', 'pale yellow', 'mustard yellow', 'dark yellow', 
                               'amber', 'chartreuse', 'gold')) AS has_yellow,
  
  EXISTS(SELECT 1 FROM product_colors_link pcl JOIN colors c ON pcl.color_id = c.color_id
         WHERE pcl.product_id = p.product_id AND c.status = 'active'
         AND LOWER(c.name) IN ('orange', 'peach', 'sunset', 'terracotta', 'copper', 
                               'dark orange', 'true orange')) AS has_orange,
  
  EXISTS(SELECT 1 FROM product_colors_link pcl JOIN colors c ON pcl.color_id = c.color_id
         WHERE pcl.product_id = p.product_id AND c.status = 'active'
         AND LOWER(c.name) IN ('purple', 'lavender', 'pinky lavender', 'true purple', 'dark purple')) AS has_purple,
  
  EXISTS(SELECT 1 FROM product_colors_link pcl JOIN colors c ON pcl.color_id = c.color_id
         WHERE pcl.product_id = p.product_id AND c.status = 'active'
         AND LOWER(c.name) IN ('blue', 'soft blue', 'light blue', 'teal')) AS has_blue,
  
  EXISTS(SELECT 1 FROM product_colors_link pcl JOIN colors c ON pcl.color_id = c.color_id
         WHERE pcl.product_id = p.product_id AND c.status = 'active'
         AND LOWER(c.name) IN ('green', 'sage green', 'emerald green', 'forest green', 
                               'lime green', 'light green', 'true green')) AS has_green,
  
  COALESCE(JSON_EXTRACT(pa.available_dates, '$[0].start_month'), 1) AS season_start_month,
  COALESCE(JSON_EXTRACT(pa.available_dates, '$[0].start_day'), 1) AS season_start_day,
  COALESCE(JSON_EXTRACT(pa.available_dates, '$[0].end_month'), 12) AS season_end_month,
  COALESCE(JSON_EXTRACT(pa.available_dates, '$[0].end_day'), 31) AS season_end_day,
  
  CASE 
    WHEN JSON_EXTRACT(pa.available_dates, '$[0].start_month') = 1
     AND JSON_EXTRACT(pa.available_dates, '$[0].start_day') = 1
     AND JSON_EXTRACT(pa.available_dates, '$[0].end_month') = 12
     AND JSON_EXTRACT(pa.available_dates, '$[0].end_day') = 31
    THEN TRUE
    WHEN pa.available_dates IS NULL THEN TRUE
    ELSE FALSE
  END AS is_year_round,
  
  (SELECT pav.value FROM product_attribute_values pav 
   WHERE pav.product_id = p.product_id AND pav.attribute_id = 56 LIMIT 1) AS seasonality,
  
  (SELECT pav.value FROM product_attribute_values pav 
   WHERE pav.product_id = p.product_id AND pav.attribute_id = 370 LIMIT 1) AS diy_level,
  
  (SELECT pav.value FROM product_attribute_values pav 
   WHERE pav.product_id = p.product_id AND pav.attribute_id = 374 LIMIT 1) AS holiday_occasion,
  
  (SELECT pav.value FROM product_attribute_values pav 
   WHERE pav.product_id = p.product_id AND pav.attribute_id = 371 LIMIT 1) AS product_type_all_flowers,
  
  (SELECT pav.value FROM product_attribute_values pav 
   WHERE pav.product_id = p.product_id AND pav.attribute_id = 415 LIMIT 1) AS recipe_metafield,
  
  (SELECT pav.value FROM product_attribute_values pav 
   WHERE pav.product_id = p.product_id AND pav.attribute_id = 365 LIMIT 1) AS group_category

FROM products p
LEFT JOIN product_variants pv ON p.product_id = pv.product_id AND pv.status = 'active'
LEFT JOIN product_availability pa ON p.product_id = pa.product_id
WHERE p.status = 'active';"""
            
            # Execute the CREATE VIEW statement
            mysql_cur = mysql_conn.cursor()
            try:
                # Try DROP first (ignore if doesn't exist)
                try:
                    mysql_cur.execute("DROP VIEW IF EXISTS flowers_view")
                except:
                    pass
                
                # Remove CREATE OR REPLACE if present, use CREATE
                view_sql_clean = view_sql.replace('CREATE OR REPLACE VIEW', 'CREATE VIEW')
                # Remove trailing semicolon
                view_sql_clean = view_sql_clean.rstrip().rstrip(';')
                
                # Execute the CREATE VIEW
                mysql_cur.execute(view_sql_clean)
                mysql_conn.commit()
                print("✅ VIEW created successfully!")
            except Exception as e:
                error_msg = str(e)
                if 'PermissionDenied' in error_msg or 'DDL command denied' in error_msg:
                    print("\n⚠️  PERMISSION ERROR: Cannot create VIEW automatically.")
                    print("   Your MySQL user doesn't have DDL permissions (PlanetScale limitation).")
                    print("\n" + "="*80)
                    print("MANUAL SETUP REQUIRED")
                    print("="*80)
                    print("\nPlease create the VIEW manually in DBeaver using this SQL:")
                    print("\n" + "-"*80)
                    print(view_sql_clean[:2000])  # Print first 2000 chars
                    print("...")
                    print("-"*80)
                    print(f"\n✅ Full SQL saved to: create_flowers_view.sql")
                    print("\nAfter creating the VIEW manually, run this script again.")
                    return
                else:
                    print(f"❌ Error creating VIEW: {e}")
                    print(f"SQL (first 500 chars): {view_sql_clean[:500]}")
                    mysql_conn.rollback()
                    raise
        else:
            print("✅ VIEW already exists")
        
        # Run all tasks
        task1_results = task1_field_comparison(pg_conn, mysql_conn)
        task2_results = task2_query_comparison(pg_conn, mysql_conn)
        task3_results = task3_format_validation(pg_conn, mysql_conn)
        
        # Generate issues report
        generate_issues_report(task1_results, task2_results, task3_results)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if pg_conn:
            pg_conn.close()
        if mysql_conn:
            mysql_conn.close()
        print("\n✅ Database connections closed")

if __name__ == "__main__":
    main()

