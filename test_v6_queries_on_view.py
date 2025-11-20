#!/usr/bin/env python3
"""
Test v6's actual SQL queries against the MySQL VIEW
This simulates what v7 will do
"""

import os
import pymysql
import psycopg2
from v6_chat_bot import MemoryState, build_sql_from_memory

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

def convert_postgres_to_mysql_sql(pg_sql):
    """Convert Postgres SQL to MySQL-compatible SQL"""
    mysql_sql = pg_sql
    
    # Replace table name
    mysql_sql = mysql_sql.replace('FROM flowers', 'FROM flowers_view')
    mysql_sql = mysql_sql.replace('FROM flowers ', 'FROM flowers_view ')
    
    # Replace boolean values
    mysql_sql = mysql_sql.replace('= true', '= 1')
    mysql_sql = mysql_sql.replace('= false', '= 0')
    mysql_sql = mysql_sql.replace('= TRUE', '= 1')
    mysql_sql = mysql_sql.replace('= FALSE', '= 0')
    mysql_sql = mysql_sql.replace('IS true', '= 1')
    mysql_sql = mysql_sql.replace('IS false', '= 0')
    
    # Replace random() with RAND()
    mysql_sql = mysql_sql.replace('random()', 'RAND()')
    mysql_sql = mysql_sql.replace('RANDOM()', 'RAND()')
    
    # Replace DISTINCT ON (Postgres) with GROUP BY (MySQL)
    # This is complex - we'll handle it case by case
    if 'DISTINCT ON' in mysql_sql:
        # For now, just remove DISTINCT ON and add GROUP BY
        # This might need more sophisticated handling
        mysql_sql = mysql_sql.replace('DISTINCT ON (product_name)', '')
        # Add GROUP BY after WHERE clause
        if 'WHERE' in mysql_sql and 'GROUP BY' not in mysql_sql:
            # Find the WHERE clause and add GROUP BY
            where_pos = mysql_sql.find('WHERE')
            if where_pos > 0:
                # Find the end of WHERE clause (before ORDER BY or LIMIT)
                end_markers = ['ORDER BY', 'LIMIT', '),']
                end_pos = len(mysql_sql)
                for marker in end_markers:
                    pos = mysql_sql.find(marker, where_pos)
                    if pos > 0 and pos < end_pos:
                        end_pos = pos
                
                # Insert GROUP BY
                group_by = ' GROUP BY product_name'
                mysql_sql = mysql_sql[:end_pos] + group_by + mysql_sql[end_pos:]
    
    return mysql_sql

def test_v6_queries():
    """Test actual v6 queries against both databases"""
    pg_conn = get_postgres_conn()
    mysql_conn = get_mysql_conn()
    
    pg_cur = pg_conn.cursor()
    mysql_cur = mysql_conn.cursor()
    
    print("="*80)
    print("TESTING V6 QUERIES ON MYSQL VIEW")
    print("="*80)
    
    # Test Case 1: Simple color filter
    print("\n1. Testing: Red flowers")
    memory = MemoryState()
    memory.colors = ["red"]
    memory.color_logic = "OR"
    
    try:
        pg_sql = build_sql_from_memory(memory)
        print(f"   Postgres SQL (first 200 chars): {pg_sql[:200]}...")
        
        # Execute on Postgres
        pg_cur.execute(pg_sql)
        pg_results = pg_cur.fetchall()
        print(f"   Postgres: {len(pg_results)} results")
        
        # Convert and execute on MySQL
        mysql_sql = convert_postgres_to_mysql_sql(pg_sql)
        print(f"   MySQL SQL (first 200 chars): {mysql_sql[:200]}...")
        
        try:
            mysql_cur.execute(mysql_sql)
            mysql_results = mysql_cur.fetchall()
            print(f"   MySQL: {len(mysql_results)} results")
            print(f"   ✅ Query executed successfully!")
        except Exception as e:
            print(f"   ❌ MySQL query failed: {e}")
            print(f"   Need to fix SQL conversion")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test Case 2: Budget filter
    print("\n2. Testing: Under $100")
    memory = MemoryState()
    memory.budget = {"max": 100}
    
    try:
        pg_sql = build_sql_from_memory(memory)
        mysql_sql = convert_postgres_to_mysql_sql(pg_sql)
        
        pg_cur.execute(pg_sql)
        pg_results = pg_cur.fetchall()
        
        mysql_cur.execute(mysql_sql)
        mysql_results = mysql_cur.fetchall()
        
        print(f"   Postgres: {len(pg_results)} results")
        print(f"   MySQL: {len(mysql_results)} results")
        print(f"   ✅ Query executed successfully!")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test Case 3: DIY level filter
    print("\n3. Testing: Ready To Go")
    memory = MemoryState()
    memory.effort_level = "Ready To Go"
    
    try:
        pg_sql = build_sql_from_memory(memory)
        mysql_sql = convert_postgres_to_mysql_sql(pg_sql)
        
        pg_cur.execute(pg_sql)
        pg_results = pg_cur.fetchall()
        
        mysql_cur.execute(mysql_sql)
        mysql_results = mysql_cur.fetchall()
        
        print(f"   Postgres: {len(pg_results)} results")
        print(f"   MySQL: {len(mysql_results)} results")
        if len(mysql_results) > 0:
            print(f"   ✅ Query executed successfully!")
        else:
            print(f"   ⚠️  No results - might be JSON array issue (need VIEW fix)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test Case 4: Holiday occasion
    print("\n4. Testing: Wedding")
    memory = MemoryState()
    memory.occasions = ["wedding"]
    
    try:
        pg_sql = build_sql_from_memory(memory)
        mysql_sql = convert_postgres_to_mysql_sql(pg_sql)
        
        pg_cur.execute(pg_sql)
        pg_results = pg_cur.fetchall()
        
        mysql_cur.execute(mysql_sql)
        mysql_results = mysql_cur.fetchall()
        
        print(f"   Postgres: {len(pg_results)} results")
        print(f"   MySQL: {len(mysql_results)} results")
        if len(mysql_results) > 0:
            print(f"   ✅ Query executed successfully!")
        else:
            print(f"   ⚠️  No results - might be JSON array issue (need VIEW fix)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test Case 5: Complex query
    print("\n5. Testing: Red AND white, under $200, for wedding")
    memory = MemoryState()
    memory.colors = ["red", "white"]
    memory.color_logic = "AND"
    memory.budget = {"max": 200}
    memory.occasions = ["wedding"]
    
    try:
        pg_sql = build_sql_from_memory(memory)
        mysql_sql = convert_postgres_to_mysql_sql(pg_sql)
        
        pg_cur.execute(pg_sql)
        pg_results = pg_cur.fetchall()
        
        mysql_cur.execute(mysql_sql)
        mysql_results = mysql_cur.fetchall()
        
        print(f"   Postgres: {len(pg_results)} results")
        print(f"   MySQL: {len(mysql_results)} results")
        print(f"   ✅ Query executed successfully!")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    pg_conn.close()
    mysql_conn.close()
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("\n✅ If all queries executed, v7 migration is ready!")
    print("⚠️  If queries failed, we need to fix SQL conversion or VIEW")

if __name__ == "__main__":
    test_v6_queries()

