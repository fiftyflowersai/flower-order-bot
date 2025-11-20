#!/usr/bin/env python3
"""
Test the fixed VIEW queries directly (without creating VIEW)
This simulates what the results will be after applying the fixes
"""

import os
import pymysql
import psycopg2

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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

def test_fixed_queries():
    pg_conn = get_postgres_conn()
    mysql_conn = get_mysql_conn()
    
    pg_cur = pg_conn.cursor()
    mysql_cur = mysql_conn.cursor()
    
    print("="*80)
    print("TESTING FIXED VIEW QUERIES (Simulated)")
    print("="*80)
    
    # Test 1: diy_level - should now return string instead of JSON array
    print("\n1. Testing diy_level (should return 'Ready To Go' not '[\"Ready To Go\"]'):")
    mysql_cur.execute('''
        SELECT 
            p.product_id,
            p.name,
            (SELECT JSON_UNQUOTE(JSON_EXTRACT(pav.value, '$[0]')) 
             FROM product_attribute_values pav
             WHERE pav.product_id = p.product_id AND pav.attribute_id = 370 LIMIT 1) AS diy_level
        FROM products p
        WHERE p.status = 'active'
          AND (SELECT pav.value FROM product_attribute_values pav
               WHERE pav.product_id = p.product_id AND pav.attribute_id = 370 LIMIT 1) IS NOT NULL
        LIMIT 5
    ''')
    print("   MySQL (FIXED):")
    for row in mysql_cur.fetchall():
        print(f"     Product {row['product_id']}: {row['name'][:40]} - diy_level: '{row['diy_level']}'")
    
    pg_cur.execute('''
        SELECT product_name, diy_level
        FROM flowers
        WHERE diy_level IS NOT NULL
        LIMIT 5
    ''')
    print("   Postgres:")
    for row in pg_cur.fetchall():
        print(f"     {row[0][:40]} - diy_level: '{row[1]}'")
    
    # Test 2: holiday_occasion
    print("\n2. Testing holiday_occasion (should return 'Wedding' not '[\"Wedding\"]'):")
    mysql_cur.execute('''
        SELECT 
            p.product_id,
            p.name,
            (SELECT JSON_UNQUOTE(JSON_EXTRACT(pav.value, '$[0]')) 
             FROM product_attribute_values pav
             WHERE pav.product_id = p.product_id AND pav.attribute_id = 374 LIMIT 1) AS holiday_occasion
        FROM products p
        WHERE p.status = 'active'
          AND (SELECT pav.value FROM product_attribute_values pav
               WHERE pav.product_id = p.product_id AND pav.attribute_id = 374 LIMIT 1) IS NOT NULL
        LIMIT 5
    ''')
    print("   MySQL (FIXED):")
    for row in mysql_cur.fetchall():
        print(f"     Product {row['product_id']}: {row['name'][:40]} - occasion: '{row['holiday_occasion']}'")
    
    pg_cur.execute('''
        SELECT product_name, holiday_occasion
        FROM flowers
        WHERE holiday_occasion IS NOT NULL
        LIMIT 5
    ''')
    print("   Postgres:")
    for row in pg_cur.fetchall():
        print(f"     {row[0][:40]} - occasion: '{row[1]}'")
    
    # Test 3: Ready To Go count
    print("\n3. Testing 'Ready To Go' count (should match now):")
    mysql_cur.execute('''
        SELECT COUNT(*) as count
        FROM products p
        WHERE p.status = 'active'
          AND (SELECT JSON_UNQUOTE(JSON_EXTRACT(pav.value, '$[0]')) 
               FROM product_attribute_values pav
               WHERE pav.product_id = p.product_id AND pav.attribute_id = 370 LIMIT 1) = 'Ready To Go'
    ''')
    mysql_count = mysql_cur.fetchone()['count']
    
    pg_cur.execute("SELECT COUNT(*) FROM flowers WHERE diy_level = 'Ready To Go'")
    pg_count = pg_cur.fetchone()[0]
    
    print(f"   Postgres: {pg_count}")
    print(f"   MySQL (FIXED): {mysql_count}")
    if pg_count == mysql_count:
        print("   ✅ MATCH!")
    else:
        print(f"   ⚠️  Difference: {mysql_count - pg_count}")
    
    # Test 4: Seasonality NULL handling
    print("\n4. Testing seasonality NULL handling:")
    mysql_cur.execute('''
        SELECT 
            COUNT(*) as total,
            COUNT(JSON_EXTRACT(pa.available_dates, '$[0].start_month')) as with_dates,
            COUNT(CASE 
                WHEN JSON_EXTRACT(pa.available_dates, '$[0].start_month') = 1
                 AND JSON_EXTRACT(pa.available_dates, '$[0].start_day') = 1
                 AND JSON_EXTRACT(pa.available_dates, '$[0].end_month') = 12
                 AND JSON_EXTRACT(pa.available_dates, '$[0].end_day') = 31
                THEN 1
            END) as year_round,
            COUNT(CASE 
                WHEN NOT (
                    JSON_EXTRACT(pa.available_dates, '$[0].start_month') = 1
                    AND JSON_EXTRACT(pa.available_dates, '$[0].start_day') = 1
                    AND JSON_EXTRACT(pa.available_dates, '$[0].end_month') = 12
                    AND JSON_EXTRACT(pa.available_dates, '$[0].end_day') = 31
                ) AND pa.available_dates IS NOT NULL
                THEN 1
            END) as seasonal
        FROM products p
        LEFT JOIN product_availability pa ON p.product_id = pa.product_id
        WHERE p.status = 'active'
    ''')
    mysql_stats = mysql_cur.fetchone()
    
    pg_cur.execute('''
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN is_year_round = true THEN 1 END) as year_round,
            COUNT(CASE WHEN is_year_round = false THEN 1 END) as seasonal
        FROM flowers
    ''')
    pg_stats = pg_cur.fetchone()
    
    print(f"   MySQL (FIXED):")
    print(f"     Total: {mysql_stats['total']}")
    print(f"     Year-round: {mysql_stats['year_round']}")
    print(f"     Seasonal: {mysql_stats['seasonal']}")
    print(f"   Postgres:")
    print(f"     Total: {pg_stats[0]}")
    print(f"     Year-round: {pg_stats[1]}")
    print(f"     Seasonal: {pg_stats[2]}")
    
    pg_conn.close()
    mysql_conn.close()
    
    print("\n" + "="*80)
    print("✅ Fixed queries tested successfully!")
    print("="*80)
    print("\nNext step: Apply the fixes by running create_flowers_view_fixed.sql in DBeaver")

if __name__ == "__main__":
    test_fixed_queries()

