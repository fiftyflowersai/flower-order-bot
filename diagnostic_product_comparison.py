#!/usr/bin/env python3
"""
Diagnostic Product ID Comparison
Compares product_id and variant_id counts between Postgres and MySQL
"""

import os
import psycopg2
import pymysql
from typing import Dict, Any, List, Tuple

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
# POSTGRES QUERIES
# ============================================================================

def run_postgres_queries(conn):
    """Run all Postgres diagnostic queries"""
    cur = conn.cursor()
    results = {}
    
    print("\n" + "="*80)
    print("POSTGRES QUERIES")
    print("="*80)
    
    # Query 1: Parse and count distinct product_ids
    print("\n[1] Parsing unique_id to extract product_ids...")
    cur.execute("""
        SELECT 
          COUNT(*) as total_rows,
          COUNT(DISTINCT FLOOR(SPLIT_PART(unique_id, '_', 1)::numeric)::int) as distinct_product_ids,
          COUNT(DISTINCT CONCAT(SPLIT_PART(unique_id, '_', 1), '_', SPLIT_PART(unique_id, '_', 2))) as distinct_product_variant_pairs
        FROM flowers
    """)
    row = cur.fetchone()
    results['pg_total_rows'] = row[0]
    results['pg_distinct_product_ids'] = row[1]
    results['pg_distinct_product_variant_pairs'] = row[2]
    print(f"  Total rows: {row[0]:,}")
    print(f"  Distinct product_ids: {row[1]:,}")
    print(f"  Distinct product+variant pairs: {row[2]:,}")
    
    # Query 2: Sample unique_ids
    print("\n[2] Sample unique_ids (first 10):")
    cur.execute("""
        SELECT 
          unique_id,
          FLOOR(SPLIT_PART(unique_id, '_', 1)::numeric)::int as extracted_product_id,
          FLOOR(SPLIT_PART(unique_id, '_', 2)::numeric)::int as extracted_variant_id,
          product_name,
          variant_name
        FROM flowers
        ORDER BY FLOOR(SPLIT_PART(unique_id, '_', 1)::numeric)::int
        LIMIT 10
    """)
    for row in cur.fetchall():
        print(f"  {row[0]} → product_id={row[1]}, variant_id={row[2]}, name={row[3][:40] if row[3] else 'N/A'}")
    
    # Query 3: Product_id range
    print("\n[3] Product_id range:")
    cur.execute("""
        SELECT 
          MIN(FLOOR(SPLIT_PART(unique_id, '_', 1)::numeric)::int) as min_product_id,
          MAX(FLOOR(SPLIT_PART(unique_id, '_', 1)::numeric)::int) as max_product_id,
          COUNT(DISTINCT FLOOR(SPLIT_PART(unique_id, '_', 1)::numeric)::int) as distinct_product_ids
        FROM flowers
    """)
    row = cur.fetchone()
    results['pg_min_product_id'] = row[0]
    results['pg_max_product_id'] = row[1]
    print(f"  Min product_id: {row[0]}")
    print(f"  Max product_id: {row[1]}")
    print(f"  Distinct product_ids: {row[1]:,}")
    
    # Query 4: Distinct base variants
    print("\n[4] Distinct product+variant pairs (base, no color expansion):")
    cur.execute("""
        SELECT 
          COUNT(DISTINCT CONCAT(SPLIT_PART(unique_id, '_', 1), '_', SPLIT_PART(unique_id, '_', 2))) as distinct_base_variants
        FROM flowers
    """)
    row = cur.fetchone()
    results['pg_distinct_base_variants'] = row[0]
    print(f"  Distinct base variants: {row[0]:,}")
    
    # Query 9: Random 100 product_ids
    print("\n[9] Random 100 product_ids (for overlap check):")
    cur.execute("""
        SELECT product_id
        FROM (
            SELECT DISTINCT FLOOR(SPLIT_PART(unique_id, '_', 1)::numeric)::int as product_id
            FROM flowers
        ) subq
        ORDER BY RANDOM()
        LIMIT 100
    """)
    pg_product_ids = [row[0] for row in cur.fetchall()]
    results['pg_sample_product_ids'] = set(pg_product_ids)
    print(f"  Retrieved {len(pg_product_ids)} product_ids")
    print(f"  Sample: {sorted(pg_product_ids)[:10]}")
    
    return results

# ============================================================================
# MYSQL QUERIES
# ============================================================================

def run_mysql_queries(conn):
    """Run all MySQL diagnostic queries"""
    cur = conn.cursor()
    results = {}
    
    print("\n" + "="*80)
    print("MYSQL QUERIES")
    print("="*80)
    
    # Query 5: Distinct product_ids
    print("\n[5] Distinct product_ids (active only):")
    cur.execute("""
        SELECT COUNT(DISTINCT product_id) as distinct_product_ids
        FROM products 
        WHERE status = 'active'
    """)
    row = cur.fetchone()
    results['mysql_distinct_product_ids'] = row['distinct_product_ids']
    print(f"  Distinct product_ids: {row['distinct_product_ids']:,}")
    
    # Query 6: Product_id range
    print("\n[6] Product_id range:")
    cur.execute("""
        SELECT 
          MIN(product_id) as min_product_id,
          MAX(product_id) as max_product_id,
          COUNT(DISTINCT product_id) as distinct_product_ids
        FROM products
        WHERE status = 'active'
    """)
    row = cur.fetchone()
    results['mysql_min_product_id'] = row['min_product_id']
    results['mysql_max_product_id'] = row['max_product_id']
    print(f"  Min product_id: {row['min_product_id']}")
    print(f"  Max product_id: {row['max_product_id']}")
    print(f"  Distinct product_ids: {row['distinct_product_ids']:,}")
    
    # Query 7: Distinct product + variant pairs
    print("\n[7] Distinct product + variant pairs:")
    cur.execute("""
        SELECT COUNT(*) as distinct_product_variant_pairs
        FROM products p
        JOIN product_variants pv ON p.product_id = pv.product_id
        WHERE p.status = 'active' AND pv.status = 'active'
    """)
    row = cur.fetchone()
    results['mysql_distinct_product_variant_pairs'] = row['distinct_product_variant_pairs']
    print(f"  Distinct product+variant pairs: {row['distinct_product_variant_pairs']:,}")
    
    # Query 8: Product_id + variant_id range
    print("\n[8] Product_id + variant_id range:")
    cur.execute("""
        SELECT 
          MIN(pv.product_variant_id) as min_variant_id,
          MAX(pv.product_variant_id) as max_variant_id,
          COUNT(DISTINCT CONCAT(p.product_id, '_', pv.product_variant_id)) as distinct_pairs
        FROM products p
        JOIN product_variants pv ON p.product_id = pv.product_id
        WHERE p.status = 'active' AND pv.status = 'active'
    """)
    row = cur.fetchone()
    results['mysql_min_variant_id'] = row['min_variant_id']
    results['mysql_max_variant_id'] = row['max_variant_id']
    print(f"  Min variant_id: {row['min_variant_id']}")
    print(f"  Max variant_id: {row['max_variant_id']}")
    print(f"  Distinct pairs: {row['distinct_pairs']:,}")
    
    # Query 9: Random 100 product_ids
    print("\n[9] Random 100 product_ids (for overlap check):")
    cur.execute("""
        SELECT DISTINCT product_id
        FROM products
        WHERE status = 'active'
        ORDER BY RAND()
        LIMIT 100
    """)
    mysql_product_ids = [row['product_id'] for row in cur.fetchall()]
    results['mysql_sample_product_ids'] = set(mysql_product_ids)
    print(f"  Retrieved {len(mysql_product_ids)} product_ids")
    print(f"  Sample: {sorted(mysql_product_ids)[:10]}")
    
    return results

# ============================================================================
# COMPARISON & ANALYSIS
# ============================================================================

def compare_results(pg_results: Dict, mysql_results: Dict):
    """Compare Postgres and MySQL results"""
    print("\n" + "="*80)
    print("COMPARISON SUMMARY")
    print("="*80)
    
    # Core comparison table
    print("\n" + "="*100)
    print("CORE COMPARISON TABLE")
    print("="*100)
    print(f"{'Metric':<45} {'Postgres':<20} {'MySQL':<20} {'Difference':<20} {'Match?':<10}")
    print("-"*100)
    
    # Distinct product_ids
    pg_pids = pg_results['pg_distinct_product_ids']
    mysql_pids = mysql_results['mysql_distinct_product_ids']
    diff_pids = mysql_pids - pg_pids
    pct_pids = (diff_pids / pg_pids * 100) if pg_pids > 0 else 0
    match_pids = "✅" if abs(pct_pids) < 10 else "❌"
    print(f"{'Distinct product_ids':<45} {pg_pids:<20,} {mysql_pids:<20,} {diff_pids:+,} ({pct_pids:+.1f}%){'':<5} {match_pids}")
    
    # Min product_id
    pg_min = pg_results['pg_min_product_id']
    mysql_min = mysql_results['mysql_min_product_id']
    match_min = "✅" if pg_min == mysql_min else "⚠️"
    print(f"{'Min product_id':<45} {pg_min:<20} {mysql_min:<20} {'N/A':<20} {match_min}")
    
    # Max product_id
    pg_max = pg_results['pg_max_product_id']
    mysql_max = mysql_results['mysql_max_product_id']
    match_max = "✅" if abs(pg_max - mysql_max) / max(pg_max, 1) < 0.1 else "⚠️"
    print(f"{'Max product_id':<45} {pg_max:<20} {mysql_max:<20} {'N/A':<20} {match_max}")
    
    # Distinct product+variant pairs
    pg_pairs = pg_results['pg_distinct_product_variant_pairs']
    mysql_pairs = mysql_results['mysql_distinct_product_variant_pairs']
    diff_pairs = mysql_pairs - pg_pairs
    pct_pairs = (diff_pairs / pg_pairs * 100) if pg_pairs > 0 else 0
    match_pairs = "✅" if abs(pct_pairs) < 20 else "⚠️"
    print(f"{'Distinct product+variant pairs':<45} {pg_pairs:<20,} {mysql_pairs:<20,} {diff_pairs:+,} ({pct_pairs:+.1f}%){'':<5} {match_pairs}")
    
    # Total rows
    pg_rows = pg_results['pg_total_rows']
    print(f"{'Total rows (with expansion)':<45} {pg_rows:<20,} {'N/A':<20} {'N/A':<20} {'N/A':<10}")
    
    print("="*100)
    
    # Analysis
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)
    
    # 1. Do distinct product_ids match?
    print("\n1. Do distinct product_ids match?")
    if abs(pct_pids) < 10:
        print("   ✅ YES - Product IDs match (within 10%)")
        print("   → Postgres just has color expansion on top")
    else:
        print(f"   ❌ NO - Product IDs differ by {abs(pct_pids):.1f}%")
        print("   → Need to understand why (different catalogs?)")
    
    # 2. Do product_id ranges overlap?
    print("\n2. Do product_id ranges overlap?")
    range_overlap = not (pg_max < mysql_min or mysql_max < pg_min)
    if range_overlap:
        overlap_start = max(pg_min, mysql_min)
        overlap_end = min(pg_max, mysql_max)
        print(f"   ✅ YES - Ranges overlap: {overlap_start} to {overlap_end}")
        print("   → Same source, MySQL is a subset")
    else:
        print(f"   ❌ NO - Ranges don't overlap")
        print(f"   → Postgres: {pg_min}-{pg_max}, MySQL: {mysql_min}-{mysql_max}")
        print("   → Different data sources")
    
    # 3. Do product+variant pairs match?
    print("\n3. Do product+variant pairs match?")
    if abs(pct_pairs) < 20:
        print("   ✅ YES - Pairs match (within 20%)")
        print("   → Just color expansion difference")
    else:
        print(f"   ⚠️  NO - Pairs differ by {abs(pct_pairs):.1f}%")
        print("   → Different variant structures")
    
    # 4. Sample overlap
    print("\n4. Sample overlap (100 random product_ids):")
    pg_sample = pg_results['pg_sample_product_ids']
    mysql_sample = mysql_results['mysql_sample_product_ids']
    overlap = pg_sample & mysql_sample
    overlap_pct = (len(overlap) / len(pg_sample) * 100) if pg_sample else 0
    print(f"   Postgres sample: {len(pg_sample)} product_ids")
    print(f"   MySQL sample: {len(mysql_sample)} product_ids")
    print(f"   Overlap: {len(overlap)} product_ids ({overlap_pct:.1f}%)")
    
    if overlap_pct >= 80:
        print("   ✅ 80%+ overlap → Same products")
    elif overlap_pct >= 50:
        print("   ⚠️  50-80% overlap → Partial match")
    else:
        print("   ❌ <50% overlap → Different data sources")
    
    # Flags
    print("\n" + "="*80)
    print("FLAGS")
    print("="*80)
    
    if abs(pct_pids) > 10:
        print("❌ CRITICAL: Distinct product_ids differ by >10% → Different product catalogs")
    else:
        print("✅ Distinct product_ids match → Same product catalog")
    
    if abs(pct_pairs) > 20:
        print("⚠️  WARNING: Product+variant pairs differ by >20% → Different variant logic")
    else:
        print("✅ Product+variant pairs match → Same variant structure")
    
    print("✅ EXPECTED: Total rows differ due to color expansion in Postgres")
    print(f"ℹ️  INFO: Product_id ranges - Postgres: {pg_min}-{pg_max}, MySQL: {mysql_min}-{mysql_max}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("="*80)
    print("DIAGNOSTIC PRODUCT ID COMPARISON")
    print("="*80)
    
    pg_conn = None
    mysql_conn = None
    
    try:
        # Connect to databases
        print("\nConnecting to databases...")
        pg_conn = get_postgres_conn()
        mysql_conn = get_mysql_conn()
        print("✅ Connected to both databases")
        
        # Run queries
        pg_results = run_postgres_queries(pg_conn)
        mysql_results = run_mysql_queries(mysql_conn)
        
        # Compare
        compare_results(pg_results, mysql_results)
        
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

