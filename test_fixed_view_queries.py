#!/usr/bin/env python3
"""
Test fixed VIEW queries directly (simulating the fixed VIEW)
This tests what the results will be after applying the fixes
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
    """Test key queries that were failing"""
    pg_conn = get_postgres_conn()
    mysql_conn = get_mysql_conn()
    
    pg_cur = pg_conn.cursor()
    mysql_cur = mysql_conn.cursor()
    
    print("="*80)
    print("TESTING FIXED VIEW QUERIES (Simulated)")
    print("="*80)
    
    tests = [
        {
            'name': 'diy_level = Ready To Go',
            'postgres': "SELECT COUNT(*) FROM flowers WHERE diy_level = 'Ready To Go'",
            'mysql': """SELECT COUNT(*) as count
                FROM products p
                WHERE p.status = 'active'
                  AND (SELECT 
                    CASE 
                      WHEN JSON_TYPE(pav.value) = 'ARRAY' AND JSON_LENGTH(pav.value) > 0 THEN
                        JSON_UNQUOTE(JSON_EXTRACT(pav.value, '$[0]'))
                      ELSE pav.value
                    END
                  FROM product_attribute_values pav
                  WHERE pav.product_id = p.product_id AND pav.attribute_id = 370 LIMIT 1) = 'Ready To Go'"""
        },
        {
            'name': 'holiday_occasion LIKE %Wedding%',
            'postgres': "SELECT COUNT(*) FROM flowers WHERE LOWER(holiday_occasion) LIKE '%wedding%'",
            'mysql': """SELECT COUNT(*) as count
                FROM products p
                WHERE p.status = 'active'
                  AND LOWER((SELECT 
                    CASE 
                      WHEN JSON_TYPE(pav.value) = 'ARRAY' AND JSON_LENGTH(pav.value) > 1 THEN
                        (SELECT GROUP_CONCAT(JSON_UNQUOTE(JSON_EXTRACT(pav.value, CONCAT('$[', idx, ']'))) SEPARATOR '; ')
                         FROM (SELECT 0 as idx UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5) indices
                         WHERE JSON_EXTRACT(pav.value, CONCAT('$[', idx, ']')) IS NOT NULL)
                      WHEN JSON_TYPE(pav.value) = 'ARRAY' AND JSON_LENGTH(pav.value) = 1 THEN
                        JSON_UNQUOTE(JSON_EXTRACT(pav.value, '$[0]'))
                      ELSE pav.value
                    END
                  FROM product_attribute_values pav
                  WHERE pav.product_id = p.product_id AND pav.attribute_id = 374 LIMIT 1)) LIKE '%wedding%'"""
        },
        {
            'name': 'Season start day IS NULL',
            'postgres': "SELECT COUNT(*) FROM flowers WHERE season_start_day IS NULL",
            'mysql': """SELECT COUNT(*) as count
                FROM products p
                LEFT JOIN product_availability pa ON p.product_id = pa.product_id
                WHERE p.status = 'active'
                  AND JSON_EXTRACT(pa.available_dates, '$[0].start_day') IS NULL"""
        },
        {
            'name': 'is_year_round IS NULL',
            'postgres': "SELECT COUNT(*) FROM flowers WHERE is_year_round IS NULL",
            'mysql': """SELECT COUNT(*) as count
                FROM products p
                LEFT JOIN product_availability pa ON p.product_id = pa.product_id
                WHERE p.status = 'active'
                  AND (CASE
                    WHEN JSON_EXTRACT(pa.available_dates, '$[0].start_month') = 1
                     AND JSON_EXTRACT(pa.available_dates, '$[0].start_day') = 1
                     AND JSON_EXTRACT(pa.available_dates, '$[0].end_month') = 12
                     AND JSON_EXTRACT(pa.available_dates, '$[0].end_day') = 31
                    THEN TRUE
                    WHEN pa.available_dates IS NULL THEN NULL
                    ELSE FALSE
                  END) IS NULL"""
        },
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            pg_cur.execute(test['postgres'])
            pg_result = pg_cur.fetchone()[0]
            
            mysql_cur.execute(test['mysql'])
            mysql_result = mysql_cur.fetchone()['count']
            
            if pg_result == mysql_result:
                print(f"✅ {test['name']}: {pg_result} (MATCH)")
                passed += 1
            else:
                print(f"❌ {test['name']}: Postgres {pg_result} vs MySQL {mysql_result} (DIFF: {mysql_result - pg_result:+})")
                failed += 1
        except Exception as e:
            print(f"❌ {test['name']}: ERROR - {e}")
            failed += 1
    
    print("\n" + "="*80)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*80)
    
    pg_conn.close()
    mysql_conn.close()

if __name__ == "__main__":
    test_fixed_queries()

