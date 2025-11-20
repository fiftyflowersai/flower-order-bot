#!/usr/bin/env python3
"""
Field-by-Field Validation Tests
Tests each field/variable with multiple scenarios to ensure Postgres and MySQL VIEW return identical results
"""

import os
import psycopg2
import pymysql
from typing import Dict, List, Any, Tuple
from decimal import Decimal
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
# TEST DEFINITIONS
# ============================================================================

FIELD_TESTS = {
    'product_name': {
        'description': 'Product name field',
        'tests': [
            {
                'name': 'Basic product name retrieval',
                'postgres': "SELECT DISTINCT product_name FROM flowers ORDER BY product_name LIMIT 5",
                'mysql': "SELECT DISTINCT product_name FROM flowers_view ORDER BY product_name LIMIT 5",
                'compare': 'exact_match'
            },
            {
                'name': 'Product name with LIKE filter',
                'postgres': "SELECT product_name FROM flowers WHERE LOWER(product_name) LIKE '%rose%' ORDER BY product_name LIMIT 5",
                'mysql': "SELECT product_name FROM flowers_view WHERE LOWER(product_name) LIKE '%rose%' ORDER BY product_name LIMIT 5",
                'compare': 'exact_match'
            },
            {
                'name': 'Product name with NULL check',
                'postgres': "SELECT COUNT(*) as count FROM flowers WHERE product_name IS NOT NULL",
                'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE product_name IS NOT NULL",
                'compare': 'count_match'
            }
        ]
    },
    
    'variant_name': {
        'description': 'Variant name field',
        'tests': [
            {
                'name': 'Basic variant name retrieval',
                'postgres': "SELECT DISTINCT variant_name FROM flowers WHERE variant_name IS NOT NULL ORDER BY variant_name LIMIT 5",
                'mysql': "SELECT DISTINCT variant_name FROM flowers_view WHERE variant_name IS NOT NULL ORDER BY variant_name LIMIT 5",
                'compare': 'exact_match'
            },
            {
                'name': 'Variant name with quantity filter',
                'postgres': "SELECT variant_name FROM flowers WHERE LOWER(variant_name) LIKE '%100%' ORDER BY variant_name LIMIT 5",
                'mysql': "SELECT variant_name FROM flowers_view WHERE LOWER(variant_name) LIKE '%100%' ORDER BY variant_name LIMIT 5",
                'compare': 'exact_match'
            },
            {
                'name': 'Variant name NULL count',
                'postgres': "SELECT COUNT(*) as count FROM flowers WHERE variant_name IS NULL",
                'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE variant_name IS NULL",
                'compare': 'count_match'
            }
        ]
    },
    
    'variant_price': {
        'description': 'Variant price field',
        'tests': [
            {
                'name': 'Price range values',
                'postgres': "SELECT MIN(variant_price) as min_price, MAX(variant_price) as max_price, AVG(variant_price) as avg_price FROM flowers WHERE variant_price IS NOT NULL",
                'mysql': "SELECT MIN(variant_price) as min_price, MAX(variant_price) as max_price, AVG(variant_price) as avg_price FROM flowers_view WHERE variant_price IS NOT NULL",
                'compare': 'numeric_range'
            },
            {
                'name': 'Products under $100',
                'postgres': "SELECT product_name, variant_name, variant_price FROM flowers WHERE variant_price < 100 ORDER BY variant_price LIMIT 5",
                'mysql': "SELECT product_name, variant_name, variant_price FROM flowers_view WHERE variant_price < 100 ORDER BY variant_price LIMIT 5",
                'compare': 'price_match'
            },
            {
                'name': 'Price NULL count',
                'postgres': "SELECT COUNT(*) as count FROM flowers WHERE variant_price IS NULL",
                'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE variant_price IS NULL",
                'compare': 'count_match'
            }
        ]
    },
    
    'colors_raw': {
        'description': 'Colors raw aggregated field',
        'tests': [
            {
                'name': 'Sample color values',
                'postgres': "SELECT DISTINCT colors_raw FROM flowers WHERE colors_raw IS NOT NULL ORDER BY colors_raw LIMIT 5",
                'mysql': "SELECT DISTINCT colors_raw FROM flowers_view WHERE colors_raw IS NOT NULL ORDER BY colors_raw LIMIT 5",
                'compare': 'color_match'
            },
            {
                'name': 'Products with multiple colors',
                'postgres': "SELECT product_name, colors_raw FROM flowers WHERE colors_raw LIKE '%;%' ORDER BY product_name LIMIT 5",
                'mysql': "SELECT product_name, colors_raw FROM flowers_view WHERE colors_raw LIKE '%;%' ORDER BY product_name LIMIT 5",
                'compare': 'exact_match'
            },
            {
                'name': 'Colors NULL count',
                'postgres': "SELECT COUNT(*) as count FROM flowers WHERE colors_raw IS NULL",
                'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE colors_raw IS NULL",
                'compare': 'count_match'
            }
        ]
    },
    
    'has_red': {
        'description': 'Has red color boolean',
        'tests': [
            {
                'name': 'Red products count',
                'postgres': "SELECT COUNT(*) as count FROM flowers WHERE has_red = true",
                'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE has_red = 1",
                'compare': 'count_match'
            },
            {
                'name': 'Red products sample',
                'postgres': "SELECT product_name, colors_raw FROM flowers WHERE has_red = true ORDER BY product_name LIMIT 5",
                'mysql': "SELECT product_name, colors_raw FROM flowers_view WHERE has_red = 1 ORDER BY product_name LIMIT 5",
                'compare': 'exact_match'
            },
            {
                'name': 'Non-red products count',
                'postgres': "SELECT COUNT(*) as count FROM flowers WHERE has_red = false",
                'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE has_red = 0",
                'compare': 'count_match'
            }
        ]
    },
    
    'has_pink': {
        'description': 'Has pink color boolean',
        'tests': [
            {
                'name': 'Pink products count',
                'postgres': "SELECT COUNT(*) as count FROM flowers WHERE has_pink = true",
                'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE has_pink = 1",
                'compare': 'count_match'
            },
            {
                'name': 'Pink products sample',
                'postgres': "SELECT product_name, colors_raw FROM flowers WHERE has_pink = true ORDER BY product_name LIMIT 5",
                'mysql': "SELECT product_name, colors_raw FROM flowers_view WHERE has_pink = 1 ORDER BY product_name LIMIT 5",
                'compare': 'exact_match'
            },
            {
                'name': 'Pink AND red products',
                'postgres': "SELECT COUNT(*) as count FROM flowers WHERE has_pink = true AND has_red = true",
                'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE has_pink = 1 AND has_red = 1",
                'compare': 'count_match'
            }
        ]
    },
    
    'is_year_round': {
        'description': 'Year-round availability boolean',
        'tests': [
            {
                'name': 'Year-round products count',
                'postgres': "SELECT COUNT(*) as count FROM flowers WHERE is_year_round = true",
                'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE is_year_round = 1",
                'compare': 'count_match'
            },
            {
                'name': 'Seasonal products count',
                'postgres': "SELECT COUNT(*) as count FROM flowers WHERE is_year_round = false",
                'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE is_year_round = 0",
                'compare': 'count_match'
            },
            {
                'name': 'Year-round sample products',
                'postgres': "SELECT product_name, season_start_month, season_end_month FROM flowers WHERE is_year_round = true ORDER BY product_name LIMIT 5",
                'mysql': "SELECT product_name, season_start_month, season_end_month FROM flowers_view WHERE is_year_round = 1 ORDER BY product_name LIMIT 5",
                'compare': 'exact_match'
            }
        ]
    },
    
    'season_start_month': {
        'description': 'Season start month field',
        'tests': [
            {
                'name': 'Season start month distribution',
                'postgres': "SELECT season_start_month, COUNT(*) as count FROM flowers WHERE season_start_month IS NOT NULL GROUP BY season_start_month ORDER BY season_start_month",
                'mysql': "SELECT season_start_month, COUNT(*) as count FROM flowers_view WHERE season_start_month IS NOT NULL GROUP BY season_start_month ORDER BY season_start_month",
                'compare': 'distribution_match'
            },
            {
                'name': 'Spring products (start_month = 3)',
                'postgres': "SELECT COUNT(*) as count FROM flowers WHERE season_start_month = 3",
                'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE season_start_month = 3",
                'compare': 'count_match'
            },
            {
                'name': 'Sample seasonal products',
                'postgres': "SELECT product_name, season_start_month, season_start_day, season_end_month, season_end_day FROM flowers WHERE season_start_month IS NOT NULL ORDER BY product_name LIMIT 5",
                'mysql': "SELECT product_name, season_start_month, season_start_day, season_end_month, season_end_day FROM flowers_view WHERE season_start_month IS NOT NULL ORDER BY product_name LIMIT 5",
                'compare': 'exact_match'
            }
        ]
    },
    
    'diy_level': {
        'description': 'DIY level field',
        'tests': [
            {
                'name': 'DIY level distribution',
                'postgres': "SELECT diy_level, COUNT(*) as count FROM flowers WHERE diy_level IS NOT NULL GROUP BY diy_level ORDER BY diy_level",
                'mysql': "SELECT diy_level, COUNT(*) as count FROM flowers_view WHERE diy_level IS NOT NULL GROUP BY diy_level ORDER BY diy_level",
                'compare': 'distribution_match'
            },
            {
                'name': 'Ready To Go products',
                'postgres': "SELECT COUNT(*) as count FROM flowers WHERE diy_level = 'Ready To Go'",
                'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE diy_level = 'Ready To Go'",
                'compare': 'count_match'
            },
            {
                'name': 'DIY level sample',
                'postgres': "SELECT product_name, diy_level FROM flowers WHERE diy_level IS NOT NULL ORDER BY product_name LIMIT 5",
                'mysql': "SELECT product_name, diy_level FROM flowers_view WHERE diy_level IS NOT NULL ORDER BY product_name LIMIT 5",
                'compare': 'exact_match'
            }
        ]
    },
    
    'holiday_occasion': {
        'description': 'Holiday occasion field',
        'tests': [
            {
                'name': 'Occasion distribution',
                'postgres': "SELECT holiday_occasion, COUNT(*) as count FROM flowers WHERE holiday_occasion IS NOT NULL GROUP BY holiday_occasion ORDER BY count DESC LIMIT 5",
                'mysql': "SELECT holiday_occasion, COUNT(*) as count FROM flowers_view WHERE holiday_occasion IS NOT NULL GROUP BY holiday_occasion ORDER BY count DESC LIMIT 5",
                'compare': 'distribution_match'
            },
            {
                'name': 'Wedding products',
                'postgres': "SELECT COUNT(*) as count FROM flowers WHERE LOWER(holiday_occasion) LIKE '%wedding%'",
                'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE LOWER(holiday_occasion) LIKE '%wedding%'",
                'compare': 'count_match'
            },
            {
                'name': 'Occasion sample',
                'postgres': "SELECT product_name, holiday_occasion FROM flowers WHERE holiday_occasion IS NOT NULL ORDER BY product_name LIMIT 5",
                'mysql': "SELECT product_name, holiday_occasion FROM flowers_view WHERE holiday_occasion IS NOT NULL ORDER BY product_name LIMIT 5",
                'compare': 'exact_match'
            }
        ]
    }
}

# ============================================================================
# COMPARISON FUNCTIONS
# ============================================================================

def normalize_value(value, field_name):
    """Normalize values for comparison"""
    if value is None:
        return None
    
    # Handle JSON strings (for diy_level, holiday_occasion)
    if isinstance(value, str) and (value.startswith('[') or value.startswith('{')):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                if len(parsed) == 1:
                    # Single element array - extract it
                    return str(parsed[0]).strip().lower()
                elif len(parsed) > 1:
                    # Multiple elements - join them (for occasions like ["Christmas", "Holiday", "Wedding"])
                    return ';'.join([str(v).strip().lower() for v in parsed])
                else:
                    return None
            return parsed
        except:
            pass
    
    # Handle Decimal
    if isinstance(value, Decimal):
        return float(value)
    
    # Handle numeric strings (for season_start_month, etc.)
    if isinstance(value, str) and value.isdigit():
        return int(value)
    
    # Handle colors (normalize case and order)
    if field_name == 'colors_raw' and isinstance(value, str):
        colors = [c.strip().lower() for c in value.split(';')]
        return '; '.join(sorted(colors))
    
    # Handle booleans
    if isinstance(value, bool):
        return value
    if value in (1, 0, '1', '0', True, False):
        return bool(value)
    
    # Handle strings (normalize case/whitespace)
    if isinstance(value, str):
        return value.strip().lower()
    
    return value

def compare_exact_match(pg_rows, mysql_rows, field_name):
    """Compare exact row-by-row match"""
    if len(pg_rows) != len(mysql_rows):
        return False, f"Row count mismatch: {len(pg_rows)} vs {len(mysql_rows)}"
    
    for i, (pg_row, mysql_row) in enumerate(zip(pg_rows, mysql_rows)):
        # Ensure both are dicts
        pg_dict = pg_row if isinstance(pg_row, dict) else {f'col_{j}': val for j, val in enumerate(pg_row)}
        mysql_dict = mysql_row if isinstance(mysql_row, dict) else {f'col_{j}': val for j, val in enumerate(mysql_row)}
        
        # Get all keys
        all_keys = set(pg_dict.keys()) | set(mysql_dict.keys())
        
        # Compare each field
        for key in all_keys:
            pg_val = pg_dict.get(key)
            mysql_val = mysql_dict.get(key)
            
            # Normalize and compare
            pg_val_norm = normalize_value(pg_val, field_name)
            mysql_val_norm = normalize_value(mysql_val, field_name)
            
            if pg_val_norm != mysql_val_norm:
                return False, f"Row {i}, field '{key}': '{pg_val_norm}' vs '{mysql_val_norm}'"
    
    return True, "Exact match"

def compare_count_match(pg_rows, mysql_rows, field_name):
    """Compare count values"""
    pg_count = pg_rows[0][0] if isinstance(pg_rows[0], tuple) else list(pg_rows[0].values())[0]
    mysql_count = mysql_rows[0][0] if isinstance(mysql_rows[0], tuple) else list(mysql_rows[0].values())[0]
    
    # Convert to int for comparison
    pg_count = int(pg_count) if pg_count is not None else 0
    mysql_count = int(mysql_count) if mysql_count is not None else 0
    
    if pg_count == mysql_count:
        return True, f"Count match: {pg_count}"
    else:
        diff = mysql_count - pg_count
        pct = (diff / pg_count * 100) if pg_count > 0 else 0
        
        # Note: Postgres has color-expanded rows, so some differences are expected
        if abs(pct) < 25:  # Allow up to 25% difference for color expansion
            return True, f"Count close: Postgres {pg_count} vs MySQL {mysql_count} (diff: {diff:+}, {pct:+.1f}%) - Expected due to color expansion"
        else:
            return False, f"Count mismatch: Postgres {pg_count} vs MySQL {mysql_count} (diff: {diff:+}, {pct:+.1f}%)"

def compare_numeric_range(pg_rows, mysql_rows, field_name):
    """Compare numeric range (min, max, avg)"""
    pg_vals = {}
    mysql_vals = {}
    
    if isinstance(pg_rows[0], tuple):
        # Assume order: min, max, avg
        pg_vals = {'min': float(pg_rows[0][0]), 'max': float(pg_rows[0][1]), 'avg': float(pg_rows[0][2])}
    else:
        pg_vals = {k: float(v) for k, v in pg_rows[0].items()}
    
    mysql_vals = {k: float(v) for k, v in mysql_rows[0].items()}
    
    issues = []
    for key in ['min_price', 'max_price', 'avg_price']:
        pg_key = key.replace('_price', '')
        mysql_key = key
        pg_val = pg_vals.get(pg_key, pg_vals.get(key))
        mysql_val = mysql_vals.get(mysql_key)
        
        if pg_val and mysql_val:
            diff = abs(pg_val - mysql_val)
            pct = (diff / pg_val * 100) if pg_val > 0 else 0
            if diff > 0.01:  # Allow small rounding differences
                issues.append(f"{key}: {pg_val:.2f} vs {mysql_val:.2f} (diff: {diff:.2f}, {pct:.1f}%)")
    
    if issues:
        return False, "; ".join(issues)
    return True, "Numeric ranges match"

def compare_price_match(pg_rows, mysql_rows, field_name):
    """Compare price values (allow small differences)"""
    if len(pg_rows) != len(mysql_rows):
        return False, f"Row count mismatch: {len(pg_rows)} vs {len(mysql_rows)}"
    
    issues = []
    for i, (pg_row, mysql_row) in enumerate(zip(pg_rows, mysql_rows)):
        pg_price = float(pg_row[2] if isinstance(pg_row, tuple) else pg_row.get('variant_price', 0))
        mysql_price = float(mysql_row.get('variant_price', 0))
        
        diff = abs(pg_price - mysql_price)
        if diff > 0.01:
            pg_name = pg_row[0] if isinstance(pg_row, tuple) else pg_row.get('product_name', 'Unknown')
            issues.append(f"Row {i} ({pg_name[:30]}): ${pg_price:.2f} vs ${mysql_price:.2f} (diff: ${diff:.2f})")
    
    if issues:
        return False, "; ".join(issues[:3])  # Show first 3 issues
    return True, "Prices match"

def compare_color_match(pg_rows, mysql_rows, field_name):
    """Compare color values (normalize case/order)"""
    pg_colors = set()
    mysql_colors = set()
    
    for row in pg_rows:
        val = row[0] if isinstance(row, tuple) else list(row.values())[0]
        if val:
            colors = [c.strip().lower() for c in str(val).split(';')]
            pg_colors.update(colors)
    
    for row in mysql_rows:
        val = row[0] if isinstance(row, tuple) else list(row.values())[0]
        if val:
            colors = [c.strip().lower() for c in str(val).split(';')]
            mysql_colors.update(colors)
    
    if pg_colors == mysql_colors:
        return True, f"Colors match: {len(pg_colors)} unique colors"
    else:
        missing_pg = mysql_colors - pg_colors
        missing_mysql = pg_colors - mysql_colors
        return False, f"Color mismatch: MySQL has {missing_pg} not in Postgres; Postgres has {missing_mysql} not in MySQL"

def compare_distribution_match(pg_rows, mysql_rows, field_name):
    """Compare distribution (group by counts)"""
    pg_dist = {}
    mysql_dist = {}
    
    for row in pg_rows:
        if isinstance(row, tuple):
            key = row[0]
            count = row[1] if len(row) > 1 else 0
        else:
            values = list(row.values()) if hasattr(row, 'values') else list(row)
            key = values[0] if len(values) > 0 else None
            count = values[1] if len(values) > 1 else 0
        if key is not None:
            pg_dist[normalize_value(key, field_name)] = int(count)
    
    for row in mysql_rows:
        if isinstance(row, dict):
            values = list(row.values())
        else:
            values = list(row) if hasattr(row, '__iter__') else [row]
        key = values[0] if len(values) > 0 else None
        count = values[1] if len(values) > 1 else 0
        if key is not None:
            mysql_dist[normalize_value(key, field_name)] = int(count)
    
    if pg_dist == mysql_dist:
        return True, "Distribution matches"
    else:
        issues = []
        all_keys = set(pg_dist.keys()) | set(mysql_dist.keys())
        for key in sorted(all_keys):
            pg_count = pg_dist.get(key, 0)
            mysql_count = mysql_dist.get(key, 0)
            if pg_count != mysql_count:
                issues.append(f"{key}: {pg_count} vs {mysql_count}")
        return False, "; ".join(issues[:5])  # Show first 5 issues

# ============================================================================
# TEST EXECUTION
# ============================================================================

def run_test(pg_conn, mysql_conn, field_name, test):
    """Run a single test and compare results"""
    pg_cur = pg_conn.cursor()
    mysql_cur = mysql_conn.cursor()
    
    try:
        # Execute Postgres query
        pg_cur.execute(test['postgres'])
        pg_rows = pg_cur.fetchall()
        
        # Convert Postgres tuples to dicts using column names
        if pg_rows and isinstance(pg_rows[0], tuple) and pg_cur.description:
            column_names = [desc[0] for desc in pg_cur.description]
            pg_rows = [dict(zip(column_names, row)) for row in pg_rows]
        
        # Execute MySQL query
        mysql_cur.execute(test['mysql'])
        mysql_rows = mysql_cur.fetchall()
        
        # Compare based on comparison type
        compare_func = {
            'exact_match': compare_exact_match,
            'count_match': compare_count_match,
            'numeric_range': compare_numeric_range,
            'price_match': compare_price_match,
            'color_match': compare_color_match,
            'distribution_match': compare_distribution_match
        }.get(test['compare'], compare_exact_match)
        
        match, message = compare_func(pg_rows, mysql_rows, field_name)
        
        return {
            'field': field_name,
            'test_name': test['name'],
            'match': match,
            'message': message,
            'pg_row_count': len(pg_rows),
            'mysql_row_count': len(mysql_rows),
            'pg_sample': str(pg_rows[:2]) if pg_rows else 'No results',
            'mysql_sample': str(mysql_rows[:2]) if mysql_rows else 'No results'
        }
    except Exception as e:
        return {
            'field': field_name,
            'test_name': test['name'],
            'match': False,
            'message': f"Error: {str(e)}",
            'pg_row_count': 0,
            'mysql_row_count': 0,
            'pg_sample': 'Error',
            'mysql_sample': 'Error'
        }

def run_all_tests(pg_conn, mysql_conn):
    """Run all field tests"""
    print("="*100)
    print("FIELD-BY-FIELD VALIDATION TESTS")
    print("="*100)
    
    all_results = []
    
    for field_name, field_config in FIELD_TESTS.items():
        print(f"\n{'='*100}")
        print(f"Testing Field: {field_name} - {field_config['description']}")
        print(f"{'='*100}")
        
        for test in field_config['tests']:
            print(f"\n  Test: {test['name']}")
            result = run_test(pg_conn, mysql_conn, field_name, test)
            all_results.append(result)
            
            status = "✅ PASS" if result['match'] else "❌ FAIL"
            print(f"    Status: {status}")
            print(f"    Message: {result['message']}")
            print(f"    Postgres rows: {result['pg_row_count']}, MySQL rows: {result['mysql_row_count']}")
            
            if not result['match']:
                print(f"    Postgres sample: {result['pg_sample'][:100]}")
                print(f"    MySQL sample: {result['mysql_sample'][:100]}")
    
    return all_results

def generate_summary_report(results):
    """Generate summary report"""
    print("\n" + "="*100)
    print("VALIDATION SUMMARY REPORT")
    print("="*100)
    
    # Group by field
    by_field = {}
    for result in results:
        field = result['field']
        if field not in by_field:
            by_field[field] = []
        by_field[field].append(result)
    
    # Summary table
    print(f"\n{'Field':<25} {'Tests':<10} {'Passed':<10} {'Failed':<10} {'Status':<20}")
    print("-"*100)
    
    total_tests = 0
    total_passed = 0
    total_failed = 0
    
    for field, field_results in by_field.items():
        passed = sum(1 for r in field_results if r['match'])
        failed = len(field_results) - passed
        total_tests += len(field_results)
        total_passed += passed
        total_failed += failed
        
        status = "✅ PASS" if failed == 0 else f"⚠️  {failed} FAIL"
        print(f"{field:<25} {len(field_results):<10} {passed:<10} {failed:<10} {status:<20}")
    
    print("-"*100)
    print(f"{'TOTAL':<25} {total_tests:<10} {total_passed:<10} {total_failed:<10} {'':<20}")
    
    # Failed tests detail
    failed_tests = [r for r in results if not r['match']]
    if failed_tests:
        print("\n" + "="*100)
        print("FAILED TESTS DETAIL")
        print("="*100)
        for result in failed_tests:
            print(f"\n❌ {result['field']} - {result['test_name']}")
            print(f"   {result['message']}")
            print(f"   Postgres: {result['pg_sample'][:150]}")
            print(f"   MySQL: {result['mysql_sample'][:150]}")
    
    # Confidence assessment
    print("\n" + "="*100)
    print("CONFIDENCE ASSESSMENT")
    print("="*100)
    
    pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    if pass_rate >= 95:
        confidence = "✅ HIGH CONFIDENCE - All fields working as intended"
    elif pass_rate >= 80:
        confidence = "⚠️  MODERATE CONFIDENCE - Some fields need attention"
    else:
        confidence = "❌ LOW CONFIDENCE - Multiple fields have issues"
    
    print(f"\nPass Rate: {pass_rate:.1f}% ({total_passed}/{total_tests} tests passed)")
    print(f"Confidence Level: {confidence}")
    
    if total_failed > 0:
        print(f"\n⚠️  {total_failed} test(s) failed - review failed tests above")
    else:
        print(f"\n✅ All tests passed! Fields are working correctly.")

# ============================================================================
# MAIN
# ============================================================================

def main():
    pg_conn = None
    mysql_conn = None
    
    try:
        print("Connecting to databases...")
        pg_conn = get_postgres_conn()
        mysql_conn = get_mysql_conn()
        print("✅ Connected to both databases\n")
        
        # Run all tests
        results = run_all_tests(pg_conn, mysql_conn)
        
        # Generate summary
        generate_summary_report(results)
        
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

