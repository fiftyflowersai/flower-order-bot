"""
Database Comparison Tool
========================
Compares the local static Postgres catalog with the live DBeaver MySQL catalog.

This script:
1. Connects to both databases
2. Compares schema structure
3. Compares data counts and distributions
4. Generates detailed comparison reports
5. Identifies discrepancies and missing data

Usage:
    python compare_databases.py

Requirements:
    - psycopg2 (for Postgres)
    - pymysql (for MySQL)
    - python-dotenv

IMPORTANT NOTES:
- The MySQL queries assume a normalized schema with tables:
  - products (main product info)
  - product_variants (variants with prices)
  - product_colors_link (color relationships)
  - product_availability (seasonality as JSON)
  - colors (color definitions)
  
- If your DBeaver schema differs, you'll need to update the MySQL queries
  in run_all_comparisons() to match your actual table/column names.

- The Postgres schema is denormalized (single 'flowers' table), while
  MySQL is normalized (multiple joined tables).
"""

import os
import psycopg2
import pymysql
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple
from collections import defaultdict

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, will use environment variables directly

# ============================================================================
# DATABASE CONNECTIONS
# ============================================================================

class DatabaseConnections:
    """Manages connections to both databases"""
    
    def __init__(self):
        # Local Static Postgres - load from environment variables
        pg_host = os.getenv("POSTGRES_HOST", "localhost")
        pg_port = int(os.getenv("POSTGRES_PORT", "5432"))
        pg_database = os.getenv("POSTGRES_DB", "flower_bot_db")
        pg_user = os.getenv("POSTGRES_USER", "postgres")
        pg_password = os.getenv("POSTGRES_PASSWORD")
        
        if not pg_password:
            raise ValueError(
                "PostgreSQL password not found in environment variables. "
                "Please set POSTGRES_PASSWORD in your .env file."
            )
        
        self.postgres_conn = psycopg2.connect(
            host=pg_host,
            port=pg_port,
            database=pg_database,
            user=pg_user,
            password=pg_password
        )
        self.postgres_cur = self.postgres_conn.cursor()
        
        # Live DBeaver MySQL (requires SSL for PlanetScale)
        # Load credentials from environment variables
        mysql_host = os.getenv("DB_HOST", "aws.connect.psdb.cloud")
        mysql_port = int(os.getenv("DB_PORT", "3306"))
        mysql_database = os.getenv("DB_NAME", "cms")
        mysql_user = os.getenv("DB_USER")
        mysql_password = os.getenv("DB_PASSWORD")
        
        if not mysql_user or not mysql_password:
            raise ValueError(
                "MySQL credentials not found in environment variables. "
                "Please set DB_USER and DB_PASSWORD in your .env file."
            )
        
        self.mysql_conn = pymysql.connect(
            host=mysql_host,
            port=mysql_port,
            database=mysql_database,
            user=mysql_user,
            password=mysql_password,
            cursorclass=pymysql.cursors.DictCursor,
            ssl={'ssl': {}}  # Enable SSL for PlanetScale
        )
        self.mysql_cur = self.mysql_conn.cursor()
    
    def close(self):
        """Close all connections"""
        self.postgres_cur.close()
        self.postgres_conn.close()
        self.mysql_cur.close()
        self.mysql_conn.close()

# ============================================================================
# FIELD COMPARISON
# ============================================================================

class FieldComparison:
    """Compares individual fields between databases"""
    
    def __init__(self, db: DatabaseConnections):
        self.db = db
        self.results = {}
    
    def compare_field(self, field_name: str, 
                     postgres_query: str, 
                     mysql_query: str,
                     description: str = ""):
        """
        Compare a specific field between databases
        
        Args:
            field_name: Name of the field (e.g., "product_count")
            postgres_query: SQL query for Postgres
            mysql_query: SQL query for MySQL
            description: Human-readable description
        """
        print(f"\n{'='*80}")
        print(f"Comparing: {field_name}")
        print(f"Description: {description}")
        print(f"{'='*80}")
        
        # Query Postgres
        print("\n[Postgres Query]")
        print(postgres_query)
        self.db.postgres_cur.execute(postgres_query)
        postgres_results = self.db.postgres_cur.fetchall()
        
        # Query MySQL
        print("\n[MySQL Query]")
        print(mysql_query)
        self.db.mysql_cur.execute(mysql_query)
        mysql_results = self.db.mysql_cur.fetchall()
        
        # Store results
        self.results[field_name] = {
            'description': description,
            'postgres': postgres_results,
            'mysql': mysql_results,
            'postgres_query': postgres_query,
            'mysql_query': mysql_query
        }
        
        # Print results
        print("\n[Postgres Results]")
        self._print_results(postgres_results)
        
        print("\n[MySQL Results]")
        self._print_results(mysql_results)
        
        # Compare
        self._compare_results(field_name, postgres_results, mysql_results)
    
    def _print_results(self, results):
        """Pretty print query results"""
        if not results:
            print("  (empty)")
            return
        
        for row in results[:10]:  # Limit to first 10 rows
            print(f"  {row}")
        
        if len(results) > 10:
            print(f"  ... and {len(results) - 10} more rows")
    
    def _compare_results(self, field_name: str, postgres_results, mysql_results):
        """Compare and analyze differences"""
        print("\n[Comparison]")
        
        if postgres_results == mysql_results:
            print("  ✅ EXACT MATCH")
            self.results[field_name]['status'] = 'MATCH'
        else:
            print("  ⚠️  DIFFERENCES FOUND")
            self.results[field_name]['status'] = 'DIFFERENT'
            
            # Analyze differences
            if isinstance(postgres_results, list) and isinstance(mysql_results, list):
                if len(postgres_results) == 1 and len(mysql_results) == 1:
                    # Single value comparison (e.g., COUNT)
                    pg_val = postgres_results[0][0] if postgres_results[0] else None
                    my_val = mysql_results[0][0] if isinstance(mysql_results[0], tuple) else mysql_results[0].get(list(mysql_results[0].keys())[0])
                    
                    if pg_val and my_val:
                        diff = my_val - pg_val
                        pct = (diff / pg_val * 100) if pg_val else 0
                        print(f"  Postgres: {pg_val}")
                        print(f"  MySQL:    {my_val}")
                        print(f"  Difference: {diff:+} ({pct:+.1f}%)")
                else:
                    print(f"  Postgres rows: {len(postgres_results)}")
                    print(f"  MySQL rows:    {len(mysql_results)}")
    
    def generate_report(self, output_file: str = "comparison_report.md"):
        """Generate markdown report of all comparisons"""
        with open(output_file, 'w') as f:
            f.write("# Database Comparison Report\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
            f.write(f"**Databases:**\n")
            f.write(f"- Local: PostgreSQL (flower_bot_db)\n")
            f.write(f"- Live: MySQL (cms)\n\n")
            
            f.write("---\n\n")
            
            # Summary
            matches = sum(1 for r in self.results.values() if r['status'] == 'MATCH')
            diffs = sum(1 for r in self.results.values() if r['status'] == 'DIFFERENT')
            
            f.write("## Summary\n\n")
            f.write(f"- ✅ Matches: {matches}\n")
            f.write(f"- ⚠️  Differences: {diffs}\n")
            f.write(f"- Total Comparisons: {len(self.results)}\n\n")
            
            f.write("---\n\n")
            
            # Detailed results
            f.write("## Detailed Comparisons\n\n")
            
            for field_name, data in self.results.items():
                status_icon = "✅" if data['status'] == 'MATCH' else "⚠️"
                f.write(f"### {status_icon} {field_name}\n\n")
                f.write(f"**Description:** {data['description']}\n\n")
                f.write(f"**Status:** {data['status']}\n\n")
                
                f.write("**Postgres Query:**\n")
                f.write(f"```sql\n{data['postgres_query']}\n```\n\n")
                
                f.write("**MySQL Query:**\n")
                f.write(f"```sql\n{data['mysql_query']}\n```\n\n")
                
                f.write("**Results:**\n")
                f.write(f"- Postgres: {len(data['postgres'])} rows\n")
                f.write(f"- MySQL: {len(data['mysql'])} rows\n\n")
                
                f.write("---\n\n")
        
        print(f"\n✅ Report generated: {output_file}")

# ============================================================================
# SCHEMA COMPARISON
# ============================================================================

def compare_schemas(db: DatabaseConnections):
    """Compare table schemas between Postgres and MySQL"""
    print("\n" + "="*80)
    print("SCHEMA COMPARISON")
    print("="*80)
    
    # Critical columns used in v6_chat_bot.py SQL queries
    critical_columns = [
        'unique_id', 'product_name', 'variant_name', 'description_clean', 
        'variant_price', 'colors_raw', 'diy_level', 'product_type_all_flowers',
        'group_category', 'recipe_metafield', 'holiday_occasion', 
        'is_year_round', 'non_color_options',
        'season_start_month', 'season_start_day', 'season_end_month', 'season_end_day',
        'season_range_2_start_month', 'season_range_2_start_day', 
        'season_range_2_end_month', 'season_range_2_end_day',
        'season_range_3_start_month', 'season_range_3_start_day',
        'season_range_3_end_month', 'season_range_3_end_day',
        'has_red', 'has_pink', 'has_white', 'has_yellow', 'has_orange',
        'has_purple', 'has_blue', 'has_green'
    ]
    
    print("\n[Postgres Schema - flowers table]")
    try:
        db.postgres_cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'flowers'
            ORDER BY column_name
        """)
        pg_columns = {row[0]: row[1] for row in db.postgres_cur.fetchall()}
        print(f"  Total columns: {len(pg_columns)}")
        
        # Check critical columns
        missing_pg = [col for col in critical_columns if col not in pg_columns]
        if missing_pg:
            print(f"  ⚠️  Missing critical columns: {missing_pg}")
        else:
            print("  ✅ All critical columns present")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        pg_columns = {}
    
    print("\n[MySQL Schema - products table]")
    try:
        db.mysql_cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'cms' AND table_name = 'products'
            ORDER BY column_name
        """)
        mysql_columns = {row['column_name']: row['data_type'] for row in db.mysql_cur.fetchall()}
        print(f"  Total columns: {len(mysql_columns)}")
        
        # Note: MySQL schema is different (normalized), so we can't directly compare
        # This is just for reference
        print("  ℹ️  MySQL uses normalized schema (products + product_variants + product_colors_link)")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        mysql_columns = {}
    
    print("\n[Column Mapping Notes]")
    print("  Postgres 'flowers' table is denormalized (single table)")
    print("  MySQL uses normalized schema:")
    print("    - products (main product info)")
    print("    - product_variants (variants with prices)")
    print("    - product_colors_link (color relationships)")
    print("    - product_availability (seasonality data)")
    print("    - colors (color definitions)")
    
    return pg_columns, mysql_columns

# ============================================================================
# PREDEFINED COMPARISONS
# ============================================================================

def run_all_comparisons(db: DatabaseConnections):
    """Run all predefined field comparisons"""
    
    comp = FieldComparison(db)
    
    # ========== BASIC COUNTS ==========
    
    comp.compare_field(
        "total_products",
        "SELECT COUNT(DISTINCT REGEXP_REPLACE(unique_id, '_color_\\d+$', '')) FROM flowers",
        "SELECT COUNT(*) FROM products WHERE status = 'active'",
        "Total number of active products (base products, not color-expanded)"
    )
    
    comp.compare_field(
        "total_variants",
        "SELECT COUNT(DISTINCT unique_id) FROM flowers",
        "SELECT COUNT(*) FROM product_variants WHERE status = 'active'",
        "Total number of active product variants"
    )
    
    # ========== COLOR STATISTICS ==========
    # Note: Postgres has color-expanded rows, so counts will be higher
    
    color_mappings = {
        'red': ['Red', 'True Red', 'Wine Red', 'Cranberry', 'Burgundy', 'Rust'],
        'pink': ['Pink', 'True Pink', 'Hot Pink', 'Dusty Pink', 'Light Pink', 'Blush', 'Dusty Rose', 'Mauve', 'Pinky Lavender', 'Fuchsia', 'Magenta', 'Coral'],
        'white': ['White', 'Ivory', 'Natural', 'Champagne', 'Clear'],
        'yellow': ['Yellow', 'Pale Yellow', 'Mustard Yellow', 'Dark Yellow', 'Amber', 'Chartreuse', 'Gold'],
        'orange': ['Orange', 'Peach', 'Sunset', 'Terracotta', 'Copper', 'Dark Orange', 'True Orange'],
        'purple': ['Purple', 'Lavender', 'Pinky Lavender', 'True Purple', 'Dark Purple'],
        'blue': ['Blue', 'Soft Blue', 'Light Blue', 'Teal'],
        'green': ['Green', 'Sage Green', 'Emerald Green', 'Forest Green', 'Lime Green', 'Light Green', 'True Green']
    }
    
    for color, variants in color_mappings.items():
        variants_str = "', '".join(variants)
        comp.compare_field(
            f"products_with_{color}",
            f"SELECT COUNT(*) FROM flowers WHERE has_{color} = true",
            f"""SELECT COUNT(DISTINCT p.product_id) 
               FROM products p
               JOIN product_colors_link pcl ON p.product_id = pcl.product_id
               JOIN colors c ON pcl.color_id = c.color_id
               WHERE p.status = 'active'
                 AND c.status = 'active'
                 AND c.name IN ('{variants_str}')""",
            f"Products with {color} color"
        )
    
    comp.compare_field(
        "products_without_colors",
        "SELECT COUNT(*) FROM flowers WHERE NOT (has_red OR has_pink OR has_white OR has_yellow OR has_orange OR has_purple OR has_blue OR has_green)",
        """SELECT COUNT(DISTINCT p.product_id)
           FROM products p
           LEFT JOIN product_colors_link pcl ON p.product_id = pcl.product_id
           WHERE p.status = 'active'
             AND pcl.product_id IS NULL""",
        "Products without any color assigned"
    )
    
    # ========== DIY LEVEL (EFFORT LEVEL) STATISTICS ==========
    # Attribute ID 370 = diy_level (stored in product_attribute_values)
    
    comp.compare_field(
        "ready_to_go_products",
        "SELECT COUNT(*) FROM flowers WHERE diy_level = 'Ready To Go'",
        """SELECT COUNT(DISTINCT pav.product_id)
           FROM product_attribute_values pav
           JOIN products p ON pav.product_id = p.product_id
           WHERE pav.attribute_id = 370
             AND p.status = 'active'
             AND LOWER(pav.value) LIKE '%ready to go%'""",
        "Products with 'Ready To Go' effort level"
    )
    
    comp.compare_field(
        "diy_in_kit_products",
        "SELECT COUNT(*) FROM flowers WHERE diy_level = 'DIY In A Kit'",
        """SELECT COUNT(DISTINCT pav.product_id)
           FROM product_attribute_values pav
           JOIN products p ON pav.product_id = p.product_id
           WHERE pav.attribute_id = 370
             AND p.status = 'active'
             AND LOWER(pav.value) LIKE '%diy in a kit%'""",
        "Products with 'DIY In A Kit' effort level"
    )
    
    comp.compare_field(
        "diy_from_scratch_products",
        "SELECT COUNT(*) FROM flowers WHERE diy_level = 'DIY From Scratch'",
        """SELECT COUNT(DISTINCT pav.product_id)
           FROM product_attribute_values pav
           JOIN products p ON pav.product_id = p.product_id
           WHERE pav.attribute_id = 370
             AND p.status = 'active'
             AND LOWER(pav.value) LIKE '%diy from scratch%'""",
        "Products with 'DIY From Scratch' effort level"
    )
    
    comp.compare_field(
        "products_without_diy_level",
        "SELECT COUNT(*) FROM flowers WHERE diy_level IS NULL",
        """SELECT COUNT(DISTINCT p.product_id)
           FROM products p
           LEFT JOIN product_attribute_values pav ON p.product_id = pav.product_id AND pav.attribute_id = 370
           WHERE p.status = 'active'
             AND pav.product_id IS NULL""",
        "Products without DIY level assigned"
    )
    
    # ========== OCCASION STATISTICS ==========
    # Attribute ID 374 = holiday_occasion (stored in product_attribute_values)
    
    comp.compare_field(
        "wedding_products",
        "SELECT COUNT(*) FROM flowers WHERE LOWER(holiday_occasion) LIKE '%wedding%'",
        """SELECT COUNT(DISTINCT pav.product_id)
           FROM product_attribute_values pav
           JOIN products p ON pav.product_id = p.product_id
           WHERE pav.attribute_id = 374
             AND p.status = 'active'
             AND LOWER(pav.value) LIKE '%wedding%'""",
        "Products tagged for weddings"
    )
    
    comp.compare_field(
        "products_with_occasions",
        "SELECT COUNT(*) FROM flowers WHERE holiday_occasion IS NOT NULL",
        """SELECT COUNT(DISTINCT pav.product_id)
           FROM product_attribute_values pav
           JOIN products p ON pav.product_id = p.product_id
           WHERE pav.attribute_id = 374
             AND p.status = 'active'
             AND pav.value IS NOT NULL
             AND pav.value != ''""",
        "Products with occasion tags"
    )
    
    comp.compare_field(
        "products_without_occasions",
        "SELECT COUNT(*) FROM flowers WHERE holiday_occasion IS NULL",
        """SELECT COUNT(DISTINCT p.product_id)
           FROM products p
           LEFT JOIN product_attribute_values pav ON p.product_id = pav.product_id AND pav.attribute_id = 374
           WHERE p.status = 'active'
             AND pav.product_id IS NULL""",
        "Products without occasion tags"
    )
    
    # ========== SEASONALITY STATISTICS ==========
    
    comp.compare_field(
        "year_round_products",
        "SELECT COUNT(*) FROM flowers WHERE is_year_round = true",
        """SELECT COUNT(DISTINCT p.product_id)
           FROM products p
           JOIN product_availability pa ON p.product_id = pa.product_id
           WHERE p.status = 'active'
             AND JSON_EXTRACT(pa.available_dates, '$[0].start_month') = 1
             AND JSON_EXTRACT(pa.available_dates, '$[0].start_day') = 1
             AND JSON_EXTRACT(pa.available_dates, '$[0].end_month') = 12
             AND JSON_EXTRACT(pa.available_dates, '$[0].end_day') = 31""",
        "Products available year-round"
    )
    
    comp.compare_field(
        "seasonal_products",
        "SELECT COUNT(*) FROM flowers WHERE is_year_round = false",
        """SELECT COUNT(DISTINCT p.product_id)
           FROM products p
           JOIN product_availability pa ON p.product_id = pa.product_id
           WHERE p.status = 'active'
             AND NOT (
               JSON_EXTRACT(pa.available_dates, '$[0].start_month') = 1
               AND JSON_EXTRACT(pa.available_dates, '$[0].start_day') = 1
               AND JSON_EXTRACT(pa.available_dates, '$[0].end_month') = 12
               AND JSON_EXTRACT(pa.available_dates, '$[0].end_day') = 31
             )""",
        "Products with seasonal availability (not year-round)"
    )
    
    comp.compare_field(
        "multi_range_seasonal_products",
        "SELECT COUNT(*) FROM flowers WHERE season_range_2_start_month IS NOT NULL",
        "SELECT 0",  # MySQL doesn't support multiple ranges in current schema
        "Products with multiple availability ranges"
    )
    
    # ========== PRICE STATISTICS ==========
    
    comp.compare_field(
        "avg_price",
        "SELECT AVG(variant_price)::numeric(10,2) FROM flowers WHERE variant_price IS NOT NULL",
        "SELECT AVG(price) FROM product_variants WHERE status = 'active' AND price IS NOT NULL",
        "Average product price"
    )
    
    comp.compare_field(
        "min_price",
        "SELECT MIN(variant_price) FROM flowers WHERE variant_price IS NOT NULL",
        "SELECT MIN(price) FROM product_variants WHERE status = 'active' AND price IS NOT NULL",
        "Minimum product price"
    )
    
    comp.compare_field(
        "max_price",
        "SELECT MAX(variant_price) FROM flowers WHERE variant_price IS NOT NULL",
        "SELECT MAX(price) FROM product_variants WHERE status = 'active' AND price IS NOT NULL",
        "Maximum product price"
    )
    
    comp.compare_field(
        "products_under_100",
        "SELECT COUNT(*) FROM flowers WHERE variant_price < 100",
        "SELECT COUNT(*) FROM product_variants WHERE status = 'active' AND price < 100",
        "Products priced under $100"
    )
    
    # ========== SAMPLE DATA COMPARISON ==========
    
    comp.compare_field(
        "sample_product_names",
        "SELECT DISTINCT product_name FROM flowers ORDER BY product_name LIMIT 10",
        "SELECT name FROM products WHERE status = 'active' ORDER BY name LIMIT 10",
        "Sample product names (first 10 alphabetically)"
    )
    
    # Generate report
    comp.generate_report("data/database_comparison_report.md")
    
    return comp

# ============================================================================
# SUMMARY TABLE GENERATION
# ============================================================================

def generate_summary_table(comp: FieldComparison):
    """Generate a formatted summary table of all comparisons"""
    print("\n" + "="*100)
    print("COMPARISON SUMMARY TABLE")
    print("="*100)
    print(f"{'Comparison':<40} {'Postgres':<15} {'MySQL':<15} {'Difference':<20} {'Status':<20}")
    print("-"*100)
    
    # Expected differences (Postgres has color-expanded rows, so counts will be higher)
    # Also, Postgres has more historical/inactive data
    expected_differences = [
        'products_with_red', 'products_with_pink', 'products_with_white', 
        'products_with_yellow', 'products_with_orange', 'products_with_purple',
        'products_with_blue', 'products_with_green', 'total_variants',
        'ready_to_go_products', 'diy_in_kit_products', 'diy_from_scratch_products',
        'wedding_products', 'products_with_occasions', 'year_round_products',
        'seasonal_products'
    ]
    
    for field_name, data in comp.results.items():
        pg_results = data['postgres']
        mysql_results = data['mysql']
        
        # Extract values
        if pg_results and len(pg_results) > 0:
            pg_val = pg_results[0][0] if isinstance(pg_results[0], tuple) else list(pg_results[0].values())[0]
        else:
            pg_val = 0
            
        if mysql_results and len(mysql_results) > 0:
            mysql_val = mysql_results[0][0] if isinstance(mysql_results[0], tuple) else list(mysql_results[0].values())[0]
        else:
            mysql_val = 0
        
        # Skip non-numeric comparisons (like sample_product_names)
        try:
            # Try to convert to numeric (handle Decimal, int, float, str)
            from decimal import Decimal
            if isinstance(pg_val, Decimal):
                pg_num = float(pg_val)
            elif pg_val is None:
                pg_num = 0
            else:
                pg_num = float(pg_val)
                
            if isinstance(mysql_val, Decimal):
                mysql_num = float(mysql_val)
            elif mysql_val is None:
                mysql_num = 0
            else:
                mysql_num = float(mysql_val)
            
            # Calculate difference
            diff = mysql_num - pg_num
            if pg_num != 0:
                pct = (diff / pg_num) * 100
                diff_str = f"{diff:+,.0f} ({pct:+.1f}%)"
            else:
                diff_str = f"{diff:+,.0f}"
            
            # Determine status
            if pg_num == mysql_num:
                status = "✅ Match"
            elif field_name in expected_differences:
                status = "⚠️  Expected Difference"
            else:
                status = "❌ Unexpected"
            
            # Format values (check if it's numeric after conversion)
            from decimal import Decimal
            if isinstance(pg_val, (int, float, Decimal)) or (isinstance(pg_val, str) and pg_val.replace('.', '').replace('-', '').isdigit()):
                pg_str = f"{pg_num:,.0f}" if pg_num == int(pg_num) else f"{pg_num:,.2f}"
            else:
                pg_str = f"{len(pg_results)} rows" if isinstance(pg_results, list) else str(pg_val)[:15]
                
            if isinstance(mysql_val, (int, float, Decimal)) or (isinstance(mysql_val, str) and mysql_val.replace('.', '').replace('-', '').isdigit()):
                mysql_str = f"{mysql_num:,.0f}" if mysql_num == int(mysql_num) else f"{mysql_num:,.2f}"
            else:
                mysql_str = f"{len(mysql_results)} rows" if isinstance(mysql_results, list) else str(mysql_val)[:15]
            
            print(f"{field_name:<40} {pg_str:<15} {mysql_str:<15} {diff_str:<20} {status:<20}")
        except (ValueError, TypeError):
            # Non-numeric comparison - just show row counts
            pg_str = f"{len(pg_results)} rows" if isinstance(pg_results, list) else "N/A"
            mysql_str = f"{len(mysql_results)} rows" if isinstance(mysql_results, list) else "N/A"
            print(f"{field_name:<40} {pg_str:<15} {mysql_str:<15} {'N/A':<20} {'ℹ️  Non-numeric':<20}")
    
    print("="*100)
    print("\nNotes:")
    print("  ✅ Match: Values are identical")
    print("  ⚠️  Expected Difference: Postgres has color-expanded rows, so counts are higher")
    print("  ❌ Unexpected: Significant difference that needs investigation")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    print("="*80)
    print("DATABASE COMPARISON TOOL")
    print("="*80)
    print("\nConnecting to databases...")
    
    try:
        db = DatabaseConnections()
        print("✅ Connected to both databases")
        
        # First, compare schemas
        compare_schemas(db)
        
        print("\nRunning data comparisons...")
        comp = run_all_comparisons(db)
        
        print("\n" + "="*80)
        print("COMPARISON COMPLETE")
        print("="*80)
        
        # Generate summary table
        generate_summary_table(comp)
        
        # Summary stats
        matches = sum(1 for r in comp.results.values() if r['status'] == 'MATCH')
        diffs = sum(1 for r in comp.results.values() if r['status'] == 'DIFFERENT')
        
        print(f"\nSummary Statistics:")
        print(f"  ✅ Matches: {matches}")
        print(f"  ⚠️  Differences: {diffs}")
        print(f"  📊 Total: {len(comp.results)}")
        
        print(f"\n📄 Detailed report: data/database_comparison_report.md")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            if 'db' in locals():
                db.close()
                print("\n✅ Database connections closed")
        except:
            pass

if __name__ == "__main__":
    main()