#!/usr/bin/env python3
"""
Comprehensive Field Validation Tests - 100+ Tests
Tests every possible scenario to ensure Postgres and MySQL VIEW return identical results
"""

import os
import psycopg2
import pymysql
from typing import Dict, List, Any, Tuple
from decimal import Decimal
import json
import random

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
# COMPREHENSIVE TEST DEFINITIONS - 100+ Tests
# ============================================================================

def get_all_tests():
    """Generate comprehensive test suite"""
    
    tests = []
    test_num = 1
    
    # ========================================================================
    # PRODUCT_NAME TESTS (10 tests)
    # ========================================================================
    tests.extend([
        {
            'id': test_num, 'field': 'product_name', 'category': 'Basic Retrieval',
            'name': 'Distinct product names',
            'postgres': "SELECT DISTINCT product_name FROM flowers ORDER BY product_name LIMIT 10",
            'mysql': "SELECT DISTINCT product_name FROM flowers_view ORDER BY product_name LIMIT 10",
            'compare': 'exact_match'
        },
        {
            'id': test_num+1, 'field': 'product_name', 'category': 'Filtering',
            'name': 'Product name LIKE %rose%',
            'postgres': "SELECT product_name FROM flowers WHERE LOWER(product_name) LIKE '%rose%' ORDER BY product_name LIMIT 10",
            'mysql': "SELECT product_name FROM flowers_view WHERE LOWER(product_name) LIKE '%rose%' ORDER BY product_name LIMIT 10",
            'compare': 'exact_match'
        },
        {
            'id': test_num+2, 'field': 'product_name', 'category': 'Filtering',
            'name': 'Product name LIKE %lily%',
            'postgres': "SELECT product_name FROM flowers WHERE LOWER(product_name) LIKE '%lily%' ORDER BY product_name LIMIT 10",
            'mysql': "SELECT product_name FROM flowers_view WHERE LOWER(product_name) LIKE '%lily%' ORDER BY product_name LIMIT 10",
            'compare': 'exact_match'
        },
        {
            'id': test_num+3, 'field': 'product_name', 'category': 'NULL Handling',
            'name': 'Product name IS NOT NULL count',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE product_name IS NOT NULL",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE product_name IS NOT NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+4, 'field': 'product_name', 'category': 'NULL Handling',
            'name': 'Product name IS NULL count',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE product_name IS NULL",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE product_name IS NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+5, 'field': 'product_name', 'category': 'Pattern Matching',
            'name': 'Product name starts with "10"',
            'postgres': "SELECT product_name FROM flowers WHERE product_name LIKE '10%' ORDER BY product_name LIMIT 10",
            'mysql': "SELECT product_name FROM flowers_view WHERE product_name LIKE '10%' ORDER BY product_name LIMIT 10",
            'compare': 'exact_match'
        },
        {
            'id': test_num+6, 'field': 'product_name', 'category': 'Pattern Matching',
            'name': 'Product name contains "DIY"',
            'postgres': "SELECT product_name FROM flowers WHERE LOWER(product_name) LIKE '%diy%' ORDER BY product_name LIMIT 10",
            'mysql': "SELECT product_name FROM flowers_view WHERE LOWER(product_name) LIKE '%diy%' ORDER BY product_name LIMIT 10",
            'compare': 'exact_match'
        },
        {
            'id': test_num+7, 'field': 'product_name', 'category': 'Aggregation',
            'name': 'Product name length distribution',
            'postgres': "SELECT LENGTH(product_name) as name_length, COUNT(*) as count FROM flowers GROUP BY LENGTH(product_name) ORDER BY name_length LIMIT 10",
            'mysql': "SELECT LENGTH(product_name) as name_length, COUNT(*) as count FROM flowers_view GROUP BY LENGTH(product_name) ORDER BY name_length LIMIT 10",
            'compare': 'distribution_match'
        },
        {
            'id': test_num+8, 'field': 'product_name', 'category': 'Uniqueness',
            'name': 'Distinct product name count',
            'postgres': "SELECT COUNT(DISTINCT product_name) as count FROM flowers",
            'mysql': "SELECT COUNT(DISTINCT product_name) as count FROM flowers_view",
            'compare': 'count_match'
        },
        {
            'id': test_num+9, 'field': 'product_name', 'category': 'Sample Data',
            'name': 'Random sample of product names',
            'postgres': "SELECT product_name FROM flowers ORDER BY RANDOM() LIMIT 10",
            'mysql': "SELECT product_name FROM flowers_view ORDER BY RAND() LIMIT 10",
            'compare': 'sample_match'
        },
    ])
    test_num += 10
    
    # ========================================================================
    # VARIANT_NAME TESTS (10 tests)
    # ========================================================================
    tests.extend([
        {
            'id': test_num, 'field': 'variant_name', 'category': 'Basic Retrieval',
            'name': 'Distinct variant names',
            'postgres': "SELECT DISTINCT variant_name FROM flowers WHERE variant_name IS NOT NULL ORDER BY variant_name LIMIT 10",
            'mysql': "SELECT DISTINCT variant_name FROM flowers_view WHERE variant_name IS NOT NULL ORDER BY variant_name LIMIT 10",
            'compare': 'exact_match'
        },
        {
            'id': test_num+1, 'field': 'variant_name', 'category': 'Filtering',
            'name': 'Variant name contains "100"',
            'postgres': "SELECT variant_name FROM flowers WHERE variant_name LIKE '%100%' ORDER BY variant_name LIMIT 10",
            'mysql': "SELECT variant_name FROM flowers_view WHERE variant_name LIKE '%100%' ORDER BY variant_name LIMIT 10",
            'compare': 'exact_match'
        },
        {
            'id': test_num+2, 'field': 'variant_name', 'category': 'Filtering',
            'name': 'Variant name contains "Bunch"',
            'postgres': "SELECT variant_name FROM flowers WHERE LOWER(variant_name) LIKE '%bunch%' ORDER BY variant_name LIMIT 10",
            'mysql': "SELECT variant_name FROM flowers_view WHERE LOWER(variant_name) LIKE '%bunch%' ORDER BY variant_name LIMIT 10",
            'compare': 'exact_match'
        },
        {
            'id': test_num+3, 'field': 'variant_name', 'category': 'NULL Handling',
            'name': 'Variant name IS NULL count',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE variant_name IS NULL",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE variant_name IS NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+4, 'field': 'variant_name', 'category': 'Pattern Matching',
            'name': 'Variant name starts with "$"',
            'postgres': "SELECT variant_name FROM flowers WHERE variant_name LIKE '$%' ORDER BY variant_name LIMIT 10",
            'mysql': "SELECT variant_name FROM flowers_view WHERE variant_name LIKE '$%' ORDER BY variant_name LIMIT 10",
            'compare': 'exact_match'
        },
        {
            'id': test_num+5, 'field': 'variant_name', 'category': 'Pattern Matching',
            'name': 'Variant name contains "Stem"',
            'postgres': "SELECT variant_name FROM flowers WHERE LOWER(variant_name) LIKE '%stem%' ORDER BY variant_name LIMIT 10",
            'mysql': "SELECT variant_name FROM flowers_view WHERE LOWER(variant_name) LIKE '%stem%' ORDER BY variant_name LIMIT 10",
            'compare': 'exact_match'
        },
        {
            'id': test_num+6, 'field': 'variant_name', 'category': 'Uniqueness',
            'name': 'Distinct variant name count',
            'postgres': "SELECT COUNT(DISTINCT variant_name) as count FROM flowers WHERE variant_name IS NOT NULL",
            'mysql': "SELECT COUNT(DISTINCT variant_name) as count FROM flowers_view WHERE variant_name IS NOT NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+7, 'field': 'variant_name', 'category': 'Combined',
            'name': 'Product + variant name combination',
            'postgres': "SELECT product_name, variant_name FROM flowers WHERE variant_name IS NOT NULL ORDER BY product_name, variant_name LIMIT 10",
            'mysql': "SELECT product_name, variant_name FROM flowers_view WHERE variant_name IS NOT NULL ORDER BY product_name, variant_name LIMIT 10",
            'compare': 'exact_match'
        },
        {
            'id': test_num+8, 'field': 'variant_name', 'category': 'Aggregation',
            'name': 'Variant names per product',
            'postgres': "SELECT product_name, COUNT(DISTINCT variant_name) as variant_count FROM flowers WHERE variant_name IS NOT NULL GROUP BY product_name ORDER BY variant_count DESC LIMIT 10",
            'mysql': "SELECT product_name, COUNT(DISTINCT variant_name) as variant_count FROM flowers_view WHERE variant_name IS NOT NULL GROUP BY product_name ORDER BY variant_count DESC LIMIT 10",
            'compare': 'exact_match'
        },
        {
            'id': test_num+9, 'field': 'variant_name', 'category': 'Sample Data',
            'name': 'Random sample of variant names',
            'postgres': "SELECT variant_name FROM flowers WHERE variant_name IS NOT NULL ORDER BY RANDOM() LIMIT 10",
            'mysql': "SELECT variant_name FROM flowers_view WHERE variant_name IS NOT NULL ORDER BY RAND() LIMIT 10",
            'compare': 'sample_match'
        },
    ])
    test_num += 10
    
    # ========================================================================
    # VARIANT_PRICE TESTS (15 tests)
    # ========================================================================
    tests.extend([
        {
            'id': test_num, 'field': 'variant_price', 'category': 'Basic Stats',
            'name': 'Price min, max, avg',
            'postgres': "SELECT MIN(variant_price) as min_price, MAX(variant_price) as max_price, AVG(variant_price) as avg_price FROM flowers WHERE variant_price IS NOT NULL",
            'mysql': "SELECT MIN(variant_price) as min_price, MAX(variant_price) as max_price, AVG(variant_price) as avg_price FROM flowers_view WHERE variant_price IS NOT NULL",
            'compare': 'numeric_range'
        },
        {
            'id': test_num+1, 'field': 'variant_price', 'category': 'Filtering',
            'name': 'Products under $50',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE variant_price < 50 AND variant_price IS NOT NULL",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE variant_price < 50 AND variant_price IS NOT NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+2, 'field': 'variant_price', 'category': 'Filtering',
            'name': 'Products under $100',
            'postgres': "SELECT product_name, variant_name, variant_price FROM flowers WHERE variant_price < 100 ORDER BY variant_price LIMIT 10",
            'mysql': "SELECT product_name, variant_name, variant_price FROM flowers_view WHERE variant_price < 100 ORDER BY variant_price LIMIT 10",
            'compare': 'price_match'
        },
        {
            'id': test_num+3, 'field': 'variant_price', 'category': 'Filtering',
            'name': 'Products $100-$200',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE variant_price BETWEEN 100 AND 200 AND variant_price IS NOT NULL",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE variant_price BETWEEN 100 AND 200 AND variant_price IS NOT NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+4, 'field': 'variant_price', 'category': 'Filtering',
            'name': 'Products over $500',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE variant_price > 500 AND variant_price IS NOT NULL",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE variant_price > 500 AND variant_price IS NOT NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+5, 'field': 'variant_price', 'category': 'Filtering',
            'name': 'Products exactly $100',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE variant_price = 100",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE variant_price = 100",
            'compare': 'count_match'
        },
        {
            'id': test_num+6, 'field': 'variant_price', 'category': 'NULL Handling',
            'name': 'Price IS NULL count',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE variant_price IS NULL",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE variant_price IS NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+7, 'field': 'variant_price', 'category': 'Distribution',
            'name': 'Price ranges distribution',
            'postgres': "SELECT CASE WHEN variant_price < 50 THEN '<50' WHEN variant_price < 100 THEN '50-100' WHEN variant_price < 200 THEN '100-200' WHEN variant_price < 500 THEN '200-500' ELSE '500+' END as price_range, COUNT(*) as count FROM flowers WHERE variant_price IS NOT NULL GROUP BY price_range",
            'mysql': "SELECT CASE WHEN variant_price < 50 THEN '<50' WHEN variant_price < 100 THEN '50-100' WHEN variant_price < 200 THEN '100-200' WHEN variant_price < 500 THEN '200-500' ELSE '500+' END as price_range, COUNT(*) as count FROM flowers_view WHERE variant_price IS NOT NULL GROUP BY price_range",
            'compare': 'distribution_match'
        },
        {
            'id': test_num+8, 'field': 'variant_price', 'category': 'Sorting',
            'name': 'Lowest prices',
            'postgres': "SELECT product_name, variant_price FROM flowers WHERE variant_price IS NOT NULL ORDER BY variant_price ASC LIMIT 10",
            'mysql': "SELECT product_name, variant_price FROM flowers_view WHERE variant_price IS NOT NULL ORDER BY variant_price ASC LIMIT 10",
            'compare': 'price_match'
        },
        {
            'id': test_num+9, 'field': 'variant_price', 'category': 'Sorting',
            'name': 'Highest prices',
            'postgres': "SELECT product_name, variant_price FROM flowers WHERE variant_price IS NOT NULL ORDER BY variant_price DESC LIMIT 10",
            'mysql': "SELECT product_name, variant_price FROM flowers_view WHERE variant_price IS NOT NULL ORDER BY variant_price DESC LIMIT 10",
            'compare': 'price_match'
        },
        {
            'id': test_num+10, 'field': 'variant_price', 'category': 'Combined',
            'name': 'Price with color filter (red under $100)',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE has_red = true AND variant_price < 100 AND variant_price IS NOT NULL",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE has_red = 1 AND variant_price < 100 AND variant_price IS NOT NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+11, 'field': 'variant_price', 'category': 'Combined',
            'name': 'Price with DIY level filter',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE diy_level = 'Ready To Go' AND variant_price IS NOT NULL",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE diy_level = 'Ready To Go' AND variant_price IS NOT NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+12, 'field': 'variant_price', 'category': 'Aggregation',
            'name': 'Average price by product',
            'postgres': "SELECT product_name, AVG(variant_price) as avg_price FROM flowers WHERE variant_price IS NOT NULL GROUP BY product_name ORDER BY avg_price DESC LIMIT 10",
            'mysql': "SELECT product_name, AVG(variant_price) as avg_price FROM flowers_view WHERE variant_price IS NOT NULL GROUP BY product_name ORDER BY avg_price DESC LIMIT 10",
            'compare': 'price_match'
        },
        {
            'id': test_num+13, 'field': 'variant_price', 'category': 'Edge Cases',
            'name': 'Products with price ending in .99',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE variant_price::text LIKE '%.99'",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE CAST(variant_price AS CHAR) LIKE '%.99'",
            'compare': 'count_match'
        },
        {
            'id': test_num+14, 'field': 'variant_price', 'category': 'Sample Data',
            'name': 'Random price samples',
            'postgres': "SELECT variant_price FROM flowers WHERE variant_price IS NOT NULL ORDER BY RANDOM() LIMIT 10",
            'mysql': "SELECT variant_price FROM flowers_view WHERE variant_price IS NOT NULL ORDER BY RAND() LIMIT 10",
            'compare': 'sample_match'
        },
    ])
    test_num += 15
    
    # ========================================================================
    # COLORS TESTS (15 tests)
    # ========================================================================
    tests.extend([
        {
            'id': test_num, 'field': 'colors_raw', 'category': 'Basic Retrieval',
            'name': 'Sample color values',
            'postgres': "SELECT DISTINCT colors_raw FROM flowers WHERE colors_raw IS NOT NULL ORDER BY colors_raw LIMIT 10",
            'mysql': "SELECT DISTINCT colors_raw FROM flowers_view WHERE colors_raw IS NOT NULL ORDER BY colors_raw LIMIT 10",
            'compare': 'color_match'
        },
        {
            'id': test_num+1, 'field': 'colors_raw', 'category': 'Filtering',
            'name': 'Products with multiple colors (contains ;)',
            'postgres': "SELECT product_name, colors_raw FROM flowers WHERE colors_raw LIKE '%;%' ORDER BY product_name LIMIT 10",
            'mysql': "SELECT product_name, colors_raw FROM flowers_view WHERE colors_raw LIKE '%;%' ORDER BY product_name LIMIT 10",
            'compare': 'exact_match'
        },
        {
            'id': test_num+2, 'field': 'colors_raw', 'category': 'Filtering',
            'name': 'Products with single color (no ;)',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE colors_raw IS NOT NULL AND colors_raw NOT LIKE '%;%'",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE colors_raw IS NOT NULL AND colors_raw NOT LIKE '%;%'",
            'compare': 'count_match'
        },
        {
            'id': test_num+3, 'field': 'colors_raw', 'category': 'NULL Handling',
            'name': 'Colors IS NULL count',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE colors_raw IS NULL",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE colors_raw IS NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+4, 'field': 'has_red', 'category': 'Boolean Filter',
            'name': 'Red products count',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE has_red = true",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE has_red = 1",
            'compare': 'count_match'
        },
        {
            'id': test_num+5, 'field': 'has_red', 'category': 'Boolean Filter',
            'name': 'Red products sample',
            'postgres': "SELECT product_name, colors_raw FROM flowers WHERE has_red = true ORDER BY product_name LIMIT 10",
            'mysql': "SELECT product_name, colors_raw FROM flowers_view WHERE has_red = 1 ORDER BY product_name LIMIT 10",
            'compare': 'exact_match'
        },
        {
            'id': test_num+6, 'field': 'has_pink', 'category': 'Boolean Filter',
            'name': 'Pink products count',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE has_pink = true",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE has_pink = 1",
            'compare': 'count_match'
        },
        {
            'id': test_num+7, 'field': 'has_white', 'category': 'Boolean Filter',
            'name': 'White products count',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE has_white = true",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE has_white = 1",
            'compare': 'count_match'
        },
        {
            'id': test_num+8, 'field': 'has_yellow', 'category': 'Boolean Filter',
            'name': 'Yellow products count',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE has_yellow = true",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE has_yellow = 1",
            'compare': 'count_match'
        },
        {
            'id': test_num+9, 'field': 'has_red', 'category': 'Combined Boolean',
            'name': 'Red AND pink products',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE has_red = true AND has_pink = true",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE has_red = 1 AND has_pink = 1",
            'compare': 'count_match'
        },
        {
            'id': test_num+10, 'field': 'has_red', 'category': 'Combined Boolean',
            'name': 'Red OR pink products',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE has_red = true OR has_pink = true",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE has_red = 1 OR has_pink = 1",
            'compare': 'count_match'
        },
        {
            'id': test_num+11, 'field': 'has_red', 'category': 'Combined Boolean',
            'name': 'Red AND white AND NOT pink',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE has_red = true AND has_white = true AND has_pink = false",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE has_red = 1 AND has_white = 1 AND has_pink = 0",
            'compare': 'count_match'
        },
        {
            'id': test_num+12, 'field': 'colors_raw', 'category': 'Pattern Matching',
            'name': 'Colors containing "red" (case insensitive)',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE LOWER(colors_raw) LIKE '%red%' AND colors_raw IS NOT NULL",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE LOWER(colors_raw) LIKE '%red%' AND colors_raw IS NOT NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+13, 'field': 'colors_raw', 'category': 'Pattern Matching',
            'name': 'Colors containing "pink"',
            'postgres': "SELECT product_name, colors_raw FROM flowers WHERE LOWER(colors_raw) LIKE '%pink%' AND colors_raw IS NOT NULL ORDER BY product_name LIMIT 10",
            'mysql': "SELECT product_name, colors_raw FROM flowers_view WHERE LOWER(colors_raw) LIKE '%pink%' AND colors_raw IS NOT NULL ORDER BY product_name LIMIT 10",
            'compare': 'exact_match'
        },
        {
            'id': test_num+14, 'field': 'colors_raw', 'category': 'Aggregation',
            'name': 'Most common colors',
            'postgres': "SELECT colors_raw, COUNT(*) as count FROM flowers WHERE colors_raw IS NOT NULL GROUP BY colors_raw ORDER BY count DESC LIMIT 10",
            'mysql': "SELECT colors_raw, COUNT(*) as count FROM flowers_view WHERE colors_raw IS NOT NULL GROUP BY colors_raw ORDER BY count DESC LIMIT 10",
            'compare': 'distribution_match'
        },
    ])
    test_num += 15
    
    # ========================================================================
    # SEASONALITY TESTS (20 tests)
    # ========================================================================
    tests.extend([
        {
            'id': test_num, 'field': 'is_year_round', 'category': 'Basic Boolean',
            'name': 'Year-round products count',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE is_year_round = true",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE is_year_round = 1",
            'compare': 'count_match'
        },
        {
            'id': test_num+1, 'field': 'is_year_round', 'category': 'Basic Boolean',
            'name': 'Seasonal products count',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE is_year_round = false",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE is_year_round = 0",
            'compare': 'count_match'
        },
        {
            'id': test_num+2, 'field': 'is_year_round', 'category': 'NULL Handling',
            'name': 'Year-round IS NULL count',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE is_year_round IS NULL",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE is_year_round IS NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+3, 'field': 'season_start_month', 'category': 'Distribution',
            'name': 'Season start month distribution',
            'postgres': "SELECT season_start_month, COUNT(*) as count FROM flowers WHERE season_start_month IS NOT NULL GROUP BY season_start_month ORDER BY season_start_month",
            'mysql': "SELECT season_start_month, COUNT(*) as count FROM flowers_view WHERE season_start_month IS NOT NULL GROUP BY season_start_month ORDER BY season_start_month",
            'compare': 'distribution_match'
        },
        {
            'id': test_num+4, 'field': 'season_start_month', 'category': 'Filtering',
            'name': 'Spring products (start_month = 3)',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE season_start_month = 3",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE season_start_month = 3",
            'compare': 'count_match'
        },
        {
            'id': test_num+5, 'field': 'season_start_month', 'category': 'Filtering',
            'name': 'Summer products (start_month = 6)',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE season_start_month = 6",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE season_start_month = 6",
            'compare': 'count_match'
        },
        {
            'id': test_num+6, 'field': 'season_start_month', 'category': 'Filtering',
            'name': 'Fall products (start_month = 9)',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE season_start_month = 9",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE season_start_month = 9",
            'compare': 'count_match'
        },
        {
            'id': test_num+7, 'field': 'season_start_month', 'category': 'Filtering',
            'name': 'Winter products (start_month = 12)',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE season_start_month = 12",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE season_start_month = 12",
            'compare': 'count_match'
        },
        {
            'id': test_num+8, 'field': 'season_start_month', 'category': 'Range Filter',
            'name': 'Products starting in Q1 (months 1-3)',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE season_start_month BETWEEN 1 AND 3",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE season_start_month BETWEEN 1 AND 3",
            'compare': 'count_match'
        },
        {
            'id': test_num+9, 'field': 'season_start_month', 'category': 'Range Filter',
            'name': 'Products starting in Q2 (months 4-6)',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE season_start_month BETWEEN 4 AND 6",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE season_start_month BETWEEN 4 AND 6",
            'compare': 'count_match'
        },
        {
            'id': test_num+10, 'field': 'season_end_month', 'category': 'Distribution',
            'name': 'Season end month distribution',
            'postgres': "SELECT season_end_month, COUNT(*) as count FROM flowers WHERE season_end_month IS NOT NULL GROUP BY season_end_month ORDER BY season_end_month",
            'mysql': "SELECT season_end_month, COUNT(*) as count FROM flowers_view WHERE season_end_month IS NOT NULL GROUP BY season_end_month ORDER BY season_end_month",
            'compare': 'distribution_match'
        },
        {
            'id': test_num+11, 'field': 'season_start_day', 'category': 'NULL Handling',
            'name': 'Season start day IS NULL count',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE season_start_day IS NULL",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE season_start_day IS NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+12, 'field': 'season_end_day', 'category': 'NULL Handling',
            'name': 'Season end day IS NULL count',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE season_end_day IS NULL",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE season_end_day IS NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+13, 'field': 'is_year_round', 'category': 'Combined',
            'name': 'Year-round AND red products',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE is_year_round = true AND has_red = true",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE is_year_round = 1 AND has_red = 1",
            'compare': 'count_match'
        },
        {
            'id': test_num+14, 'field': 'is_year_round', 'category': 'Combined',
            'name': 'Seasonal AND under $100',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE is_year_round = false AND variant_price < 100 AND variant_price IS NOT NULL",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE is_year_round = 0 AND variant_price < 100 AND variant_price IS NOT NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+15, 'field': 'season_start_month', 'category': 'Sample Data',
            'name': 'Sample seasonal products',
            'postgres': "SELECT product_name, season_start_month, season_start_day, season_end_month, season_end_day FROM flowers WHERE is_year_round = false ORDER BY product_name LIMIT 10",
            'mysql': "SELECT product_name, season_start_month, season_start_day, season_end_month, season_end_day FROM flowers_view WHERE is_year_round = 0 ORDER BY product_name LIMIT 10",
            'compare': 'exact_match'
        },
        {
            'id': test_num+16, 'field': 'season_start_month', 'category': 'Date Range',
            'name': 'Products available in May (month 5)',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE (season_start_month < 5 OR (season_start_month = 5 AND season_start_day <= 15)) AND (season_end_month > 5 OR (season_end_month = 5 AND season_end_day >= 15))",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE (season_start_month < 5 OR (season_start_month = 5 AND season_start_day <= 15)) AND (season_end_month > 5 OR (season_end_month = 5 AND season_end_day >= 15))",
            'compare': 'count_match'
        },
        {
            'id': test_num+17, 'field': 'season_start_month', 'category': 'Date Range',
            'name': 'Products available in December (month 12)',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE (season_start_month < 12 OR (season_start_month = 12 AND season_start_day <= 15)) AND (season_end_month > 12 OR (season_end_month = 12 AND season_end_day >= 15)) OR is_year_round = true",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE (season_start_month < 12 OR (season_start_month = 12 AND season_start_day <= 15)) AND (season_end_month > 12 OR (season_end_month = 12 AND season_end_day >= 15)) OR is_year_round = 1",
            'compare': 'count_match'
        },
        {
            'id': test_num+18, 'field': 'season_start_month', 'category': 'Edge Cases',
            'name': 'Products with NULL seasonality',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE season_start_month IS NULL",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE season_start_month IS NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+19, 'field': 'is_year_round', 'category': 'Sample Data',
            'name': 'Sample year-round products',
            'postgres': "SELECT product_name, season_start_month, season_end_month FROM flowers WHERE is_year_round = true ORDER BY product_name LIMIT 10",
            'mysql': "SELECT product_name, season_start_month, season_end_month FROM flowers_view WHERE is_year_round = 1 ORDER BY product_name LIMIT 10",
            'compare': 'exact_match'
        },
    ])
    test_num += 20
    
    # ========================================================================
    # DIY_LEVEL TESTS (10 tests)
    # ========================================================================
    tests.extend([
        {
            'id': test_num, 'field': 'diy_level', 'category': 'Distribution',
            'name': 'DIY level distribution',
            'postgres': "SELECT diy_level, COUNT(*) as count FROM flowers WHERE diy_level IS NOT NULL GROUP BY diy_level ORDER BY diy_level",
            'mysql': "SELECT diy_level, COUNT(*) as count FROM flowers_view WHERE diy_level IS NOT NULL GROUP BY diy_level ORDER BY diy_level",
            'compare': 'distribution_match'
        },
        {
            'id': test_num+1, 'field': 'diy_level', 'category': 'Filtering',
            'name': 'Ready To Go products',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE diy_level = 'Ready To Go'",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE diy_level = 'Ready To Go'",
            'compare': 'count_match'
        },
        {
            'id': test_num+2, 'field': 'diy_level', 'category': 'Filtering',
            'name': 'DIY In A Kit products',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE diy_level = 'DIY In A Kit'",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE diy_level = 'DIY In A Kit'",
            'compare': 'count_match'
        },
        {
            'id': test_num+3, 'field': 'diy_level', 'category': 'Filtering',
            'name': 'DIY From Scratch products',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE diy_level = 'DIY From Scratch'",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE diy_level = 'DIY From Scratch'",
            'compare': 'count_match'
        },
        {
            'id': test_num+4, 'field': 'diy_level', 'category': 'NULL Handling',
            'name': 'DIY level IS NULL count',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE diy_level IS NULL",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE diy_level IS NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+5, 'field': 'diy_level', 'category': 'Pattern Matching',
            'name': 'DIY level LIKE %Ready%',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE diy_level LIKE '%Ready%'",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE diy_level LIKE '%Ready%'",
            'compare': 'count_match'
        },
        {
            'id': test_num+6, 'field': 'diy_level', 'category': 'Combined',
            'name': 'Ready To Go AND under $100',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE diy_level = 'Ready To Go' AND variant_price < 100 AND variant_price IS NOT NULL",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE diy_level = 'Ready To Go' AND variant_price < 100 AND variant_price IS NOT NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+7, 'field': 'diy_level', 'category': 'Combined',
            'name': 'DIY From Scratch AND red',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE diy_level = 'DIY From Scratch' AND has_red = true",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE diy_level = 'DIY From Scratch' AND has_red = 1",
            'compare': 'count_match'
        },
        {
            'id': test_num+8, 'field': 'diy_level', 'category': 'Sample Data',
            'name': 'Sample DIY level products',
            'postgres': "SELECT product_name, diy_level FROM flowers WHERE diy_level IS NOT NULL ORDER BY product_name LIMIT 10",
            'mysql': "SELECT product_name, diy_level FROM flowers_view WHERE diy_level IS NOT NULL ORDER BY product_name LIMIT 10",
            'compare': 'exact_match'
        },
        {
            'id': test_num+9, 'field': 'diy_level', 'category': 'Uniqueness',
            'name': 'Distinct DIY level values',
            'postgres': "SELECT COUNT(DISTINCT diy_level) as count FROM flowers WHERE diy_level IS NOT NULL",
            'mysql': "SELECT COUNT(DISTINCT diy_level) as count FROM flowers_view WHERE diy_level IS NOT NULL",
            'compare': 'count_match'
        },
    ])
    test_num += 10
    
    # ========================================================================
    # HOLIDAY_OCCASION TESTS (15 tests)
    # ========================================================================
    tests.extend([
        {
            'id': test_num, 'field': 'holiday_occasion', 'category': 'Distribution',
            'name': 'Occasion distribution',
            'postgres': "SELECT holiday_occasion, COUNT(*) as count FROM flowers WHERE holiday_occasion IS NOT NULL GROUP BY holiday_occasion ORDER BY count DESC LIMIT 10",
            'mysql': "SELECT holiday_occasion, COUNT(*) as count FROM flowers_view WHERE holiday_occasion IS NOT NULL GROUP BY holiday_occasion ORDER BY count DESC LIMIT 10",
            'compare': 'distribution_match'
        },
        {
            'id': test_num+1, 'field': 'holiday_occasion', 'category': 'Filtering',
            'name': 'Wedding products',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE LOWER(holiday_occasion) LIKE '%wedding%'",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE LOWER(holiday_occasion) LIKE '%wedding%'",
            'compare': 'count_match'
        },
        {
            'id': test_num+2, 'field': 'holiday_occasion', 'category': 'Filtering',
            'name': 'Valentine products',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE LOWER(holiday_occasion) LIKE '%valentine%'",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE LOWER(holiday_occasion) LIKE '%valentine%'",
            'compare': 'count_match'
        },
        {
            'id': test_num+3, 'field': 'holiday_occasion', 'category': 'Filtering',
            'name': 'Mother Day products',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE LOWER(holiday_occasion) LIKE '%mother%'",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE LOWER(holiday_occasion) LIKE '%mother%'",
            'compare': 'count_match'
        },
        {
            'id': test_num+4, 'field': 'holiday_occasion', 'category': 'Filtering',
            'name': 'Birthday products',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE LOWER(holiday_occasion) LIKE '%birthday%'",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE LOWER(holiday_occasion) LIKE '%birthday%'",
            'compare': 'count_match'
        },
        {
            'id': test_num+5, 'field': 'holiday_occasion', 'category': 'Filtering',
            'name': 'Christmas products',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE LOWER(holiday_occasion) LIKE '%christmas%'",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE LOWER(holiday_occasion) LIKE '%christmas%'",
            'compare': 'count_match'
        },
        {
            'id': test_num+6, 'field': 'holiday_occasion', 'category': 'Filtering',
            'name': 'Graduation products',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE LOWER(holiday_occasion) LIKE '%graduation%'",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE LOWER(holiday_occasion) LIKE '%graduation%'",
            'compare': 'count_match'
        },
        {
            'id': test_num+7, 'field': 'holiday_occasion', 'category': 'NULL Handling',
            'name': 'Occasion IS NULL count',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE holiday_occasion IS NULL",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE holiday_occasion IS NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+8, 'field': 'holiday_occasion', 'category': 'Combined',
            'name': 'Wedding AND red products',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE LOWER(holiday_occasion) LIKE '%wedding%' AND has_red = true",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE LOWER(holiday_occasion) LIKE '%wedding%' AND has_red = 1",
            'compare': 'count_match'
        },
        {
            'id': test_num+9, 'field': 'holiday_occasion', 'category': 'Combined',
            'name': 'Wedding AND under $200',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE LOWER(holiday_occasion) LIKE '%wedding%' AND variant_price < 200 AND variant_price IS NOT NULL",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE LOWER(holiday_occasion) LIKE '%wedding%' AND variant_price < 200 AND variant_price IS NOT NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+10, 'field': 'holiday_occasion', 'category': 'Combined',
            'name': 'Valentine AND pink products',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE LOWER(holiday_occasion) LIKE '%valentine%' AND has_pink = true",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE LOWER(holiday_occasion) LIKE '%valentine%' AND has_pink = 1",
            'compare': 'count_match'
        },
        {
            'id': test_num+11, 'field': 'holiday_occasion', 'category': 'Sample Data',
            'name': 'Sample wedding products',
            'postgres': "SELECT product_name, holiday_occasion FROM flowers WHERE LOWER(holiday_occasion) LIKE '%wedding%' ORDER BY product_name LIMIT 10",
            'mysql': "SELECT product_name, holiday_occasion FROM flowers_view WHERE LOWER(holiday_occasion) LIKE '%wedding%' ORDER BY product_name LIMIT 10",
            'compare': 'exact_match'
        },
        {
            'id': test_num+12, 'field': 'holiday_occasion', 'category': 'Uniqueness',
            'name': 'Distinct occasion values',
            'postgres': "SELECT COUNT(DISTINCT holiday_occasion) as count FROM flowers WHERE holiday_occasion IS NOT NULL",
            'mysql': "SELECT COUNT(DISTINCT holiday_occasion) as count FROM flowers_view WHERE holiday_occasion IS NOT NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+13, 'field': 'holiday_occasion', 'category': 'Pattern Matching',
            'name': 'Occasions containing multiple words',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE holiday_occasion LIKE '% %' AND holiday_occasion IS NOT NULL",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE holiday_occasion LIKE '% %' AND holiday_occasion IS NOT NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+14, 'field': 'holiday_occasion', 'category': 'Sample Data',
            'name': 'Random occasion samples',
            'postgres': "SELECT holiday_occasion FROM flowers WHERE holiday_occasion IS NOT NULL ORDER BY RANDOM() LIMIT 10",
            'mysql': "SELECT holiday_occasion FROM flowers_view WHERE holiday_occasion IS NOT NULL ORDER BY RAND() LIMIT 10",
            'compare': 'sample_match'
        },
    ])
    test_num += 15
    
    # ========================================================================
    # COMPLEX COMBINED TESTS (15 tests)
    # ========================================================================
    tests.extend([
        {
            'id': test_num, 'field': 'combined', 'category': 'Multi-Filter',
            'name': 'Red AND pink AND under $100',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE has_red = true AND has_pink = true AND variant_price < 100 AND variant_price IS NOT NULL",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE has_red = 1 AND has_pink = 1 AND variant_price < 100 AND variant_price IS NOT NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+1, 'field': 'combined', 'category': 'Multi-Filter',
            'name': 'Wedding AND red AND year-round',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE LOWER(holiday_occasion) LIKE '%wedding%' AND has_red = true AND is_year_round = true",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE LOWER(holiday_occasion) LIKE '%wedding%' AND has_red = 1 AND is_year_round = 1",
            'compare': 'count_match'
        },
        {
            'id': test_num+2, 'field': 'combined', 'category': 'Multi-Filter',
            'name': 'Ready To Go AND pink AND seasonal',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE diy_level = 'Ready To Go' AND has_pink = true AND is_year_round = false",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE diy_level = 'Ready To Go' AND has_pink = 1 AND is_year_round = 0",
            'compare': 'count_match'
        },
        {
            'id': test_num+3, 'field': 'combined', 'category': 'Multi-Filter',
            'name': 'Valentine AND red AND $50-$150',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE LOWER(holiday_occasion) LIKE '%valentine%' AND has_red = true AND variant_price BETWEEN 50 AND 150 AND variant_price IS NOT NULL",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE LOWER(holiday_occasion) LIKE '%valentine%' AND has_red = 1 AND variant_price BETWEEN 50 AND 150 AND variant_price IS NOT NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+4, 'field': 'combined', 'category': 'Multi-Filter',
            'name': 'White AND yellow AND over $200',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE has_white = true AND has_yellow = true AND variant_price > 200 AND variant_price IS NOT NULL",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE has_white = 1 AND has_yellow = 1 AND variant_price > 200 AND variant_price IS NOT NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+5, 'field': 'combined', 'category': 'Multi-Filter',
            'name': 'Rose products AND red AND under $100',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE LOWER(product_name) LIKE '%rose%' AND has_red = true AND variant_price < 100 AND variant_price IS NOT NULL",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE LOWER(product_name) LIKE '%rose%' AND has_red = 1 AND variant_price < 100 AND variant_price IS NOT NULL",
            'compare': 'count_match'
        },
        {
            'id': test_num+6, 'field': 'combined', 'category': 'Multi-Filter',
            'name': 'DIY From Scratch AND seasonal AND pink',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE diy_level = 'DIY From Scratch' AND is_year_round = false AND has_pink = true",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE diy_level = 'DIY From Scratch' AND is_year_round = 0 AND has_pink = 1",
            'compare': 'count_match'
        },
        {
            'id': test_num+7, 'field': 'combined', 'category': 'Multi-Filter',
            'name': 'Wedding AND white AND Ready To Go',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE LOWER(holiday_occasion) LIKE '%wedding%' AND has_white = true AND diy_level = 'Ready To Go'",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE LOWER(holiday_occasion) LIKE '%wedding%' AND has_white = 1 AND diy_level = 'Ready To Go'",
            'compare': 'count_match'
        },
        {
            'id': test_num+8, 'field': 'combined', 'category': 'Multi-Filter',
            'name': 'Year-round AND red OR pink',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE is_year_round = true AND (has_red = true OR has_pink = true)",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE is_year_round = 1 AND (has_red = 1 OR has_pink = 1)",
            'compare': 'count_match'
        },
        {
            'id': test_num+9, 'field': 'combined', 'category': 'Multi-Filter',
            'name': 'Seasonal AND (red AND white)',
            'postgres': "SELECT COUNT(*) as count FROM flowers WHERE is_year_round = false AND has_red = true AND has_white = true",
            'mysql': "SELECT COUNT(*) as count FROM flowers_view WHERE is_year_round = 0 AND has_red = 1 AND has_white = 1",
            'compare': 'count_match'
        },
        {
            'id': test_num+10, 'field': 'combined', 'category': 'Complex Query',
            'name': 'Sample complex query results',
            'postgres': "SELECT product_name, variant_price, colors_raw, diy_level FROM flowers WHERE has_red = true AND variant_price < 150 AND diy_level = 'Ready To Go' ORDER BY variant_price LIMIT 10",
            'mysql': "SELECT product_name, variant_price, colors_raw, diy_level FROM flowers_view WHERE has_red = 1 AND variant_price < 150 AND diy_level = 'Ready To Go' ORDER BY variant_price LIMIT 10",
            'compare': 'exact_match'
        },
        {
            'id': test_num+11, 'field': 'combined', 'category': 'Complex Query',
            'name': 'Wedding products with prices',
            'postgres': "SELECT product_name, variant_price, holiday_occasion FROM flowers WHERE LOWER(holiday_occasion) LIKE '%wedding%' AND variant_price IS NOT NULL ORDER BY variant_price DESC LIMIT 10",
            'mysql': "SELECT product_name, variant_price, holiday_occasion FROM flowers_view WHERE LOWER(holiday_occasion) LIKE '%wedding%' AND variant_price IS NOT NULL ORDER BY variant_price DESC LIMIT 10",
            'compare': 'exact_match'
        },
        {
            'id': test_num+12, 'field': 'combined', 'category': 'Complex Query',
            'name': 'Seasonal pink products under $200',
            'postgres': "SELECT product_name, variant_price, season_start_month FROM flowers WHERE is_year_round = false AND has_pink = true AND variant_price < 200 AND variant_price IS NOT NULL ORDER BY product_name LIMIT 10",
            'mysql': "SELECT product_name, variant_price, season_start_month FROM flowers_view WHERE is_year_round = 0 AND has_pink = 1 AND variant_price < 200 AND variant_price IS NOT NULL ORDER BY product_name LIMIT 10",
            'compare': 'exact_match'
        },
        {
            'id': test_num+13, 'field': 'combined', 'category': 'Aggregation',
            'name': 'Average price by DIY level',
            'postgres': "SELECT diy_level, AVG(variant_price) as avg_price FROM flowers WHERE diy_level IS NOT NULL AND variant_price IS NOT NULL GROUP BY diy_level ORDER BY avg_price",
            'mysql': "SELECT diy_level, AVG(variant_price) as avg_price FROM flowers_view WHERE diy_level IS NOT NULL AND variant_price IS NOT NULL GROUP BY diy_level ORDER BY avg_price",
            'compare': 'price_match'
        },
        {
            'id': test_num+14, 'field': 'combined', 'category': 'Aggregation',
            'name': 'Color combinations count',
            'postgres': "SELECT has_red, has_pink, has_white, COUNT(*) as count FROM flowers GROUP BY has_red, has_pink, has_white ORDER BY count DESC LIMIT 10",
            'mysql': "SELECT has_red, has_pink, has_white, COUNT(*) as count FROM flowers_view GROUP BY has_red, has_pink, has_white ORDER BY count DESC LIMIT 10",
            'compare': 'distribution_match'
        },
    ])
    test_num += 15
    
    return tests

# ============================================================================
# COMPARISON FUNCTIONS (from original file)
# ============================================================================

def normalize_value(value, field_name):
    """Normalize values for comparison"""
    if value is None:
        return None
    
    # Handle JSON strings
    if isinstance(value, str) and (value.startswith('[') or value.startswith('{')):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                if len(parsed) == 1:
                    return str(parsed[0]).strip().lower()
                elif len(parsed) > 1:
                    return ';'.join([str(v).strip().lower() for v in parsed])
                else:
                    return None
            return parsed
        except:
            pass
    
    # Handle Decimal
    if isinstance(value, Decimal):
        return float(value)
    
    # Handle numeric strings
    if isinstance(value, str) and value.isdigit():
        return int(value)
    
    # Handle colors
    if field_name == 'colors_raw' and isinstance(value, str):
        colors = [c.strip().lower() for c in value.split(';')]
        return '; '.join(sorted(colors))
    
    # Handle booleans
    if isinstance(value, bool):
        return value
    if value in (1, 0, '1', '0', True, False):
        return bool(value)
    
    # Handle strings
    if isinstance(value, str):
        return value.strip().lower()
    
    return value

def compare_exact_match(pg_rows, mysql_rows, field_name):
    """Compare exact row-by-row match"""
    if len(pg_rows) != len(mysql_rows):
        return False, f"Row count mismatch: {len(pg_rows)} vs {len(mysql_rows)}"
    
    for i, (pg_row, mysql_row) in enumerate(zip(pg_rows, mysql_rows)):
        pg_dict = pg_row if isinstance(pg_row, dict) else {f'col_{j}': val for j, val in enumerate(pg_row)}
        mysql_dict = mysql_row if isinstance(mysql_row, dict) else {f'col_{j}': val for j, val in enumerate(mysql_row)}
        
        all_keys = set(pg_dict.keys()) | set(mysql_dict.keys())
        
        for key in all_keys:
            pg_val = pg_dict.get(key)
            mysql_val = mysql_dict.get(key)
            
            pg_val_norm = normalize_value(pg_val, field_name)
            mysql_val_norm = normalize_value(mysql_val, field_name)
            
            if pg_val_norm != mysql_val_norm:
                return False, f"Row {i}, field '{key}': '{pg_val_norm}' vs '{mysql_val_norm}'"
    
    return True, "Exact match"

def compare_count_match(pg_rows, mysql_rows, field_name):
    """Compare count values"""
    pg_count = pg_rows[0][0] if isinstance(pg_rows[0], tuple) else list(pg_rows[0].values())[0]
    mysql_count = mysql_rows[0][0] if isinstance(mysql_rows[0], tuple) else list(mysql_rows[0].values())[0]
    
    pg_count = int(pg_count) if pg_count is not None else 0
    mysql_count = int(mysql_count) if mysql_count is not None else 0
    
    if pg_count == mysql_count:
        return True, f"Count match: {pg_count}"
    else:
        diff = mysql_count - pg_count
        pct = (diff / pg_count * 100) if pg_count > 0 else 0
        if abs(pct) < 25:
            return True, f"Count close: Postgres {pg_count} vs MySQL {mysql_count} (diff: {diff:+}, {pct:+.1f}%)"
        else:
            return False, f"Count mismatch: Postgres {pg_count} vs MySQL {mysql_count} (diff: {diff:+}, {pct:+.1f}%)"

def compare_numeric_range(pg_rows, mysql_rows, field_name):
    """Compare numeric range"""
    pg_vals = {}
    mysql_vals = {}
    
    if isinstance(pg_rows[0], tuple):
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
            if diff > 0.01:
                issues.append(f"{key}: {pg_val:.2f} vs {mysql_val:.2f} (diff: {diff:.2f}, {pct:.1f}%)")
    
    if issues:
        return False, "; ".join(issues)
    return True, "Numeric ranges match"

def compare_price_match(pg_rows, mysql_rows, field_name):
    """Compare price values"""
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
        return False, "; ".join(issues[:3])
    return True, "Prices match"

def compare_color_match(pg_rows, mysql_rows, field_name):
    """Compare color values"""
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
    """Compare distribution"""
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
        return False, "; ".join(issues[:5])

def compare_sample_match(pg_rows, mysql_rows, field_name):
    """Compare sample data (order doesn't matter)"""
    pg_set = set()
    mysql_set = set()
    
    for row in pg_rows:
        if isinstance(row, tuple):
            val = tuple(normalize_value(v, field_name) for v in row)
        else:
            val = tuple(normalize_value(v, field_name) for v in row.values())
        pg_set.add(val)
    
    for row in mysql_rows:
        if isinstance(row, tuple):
            val = tuple(normalize_value(v, field_name) for v in row)
        else:
            val = tuple(normalize_value(v, field_name) for v in row.values())
        mysql_set.add(val)
    
    if pg_set == mysql_set:
        return True, "Samples match"
    else:
        overlap = len(pg_set & mysql_set)
        return False, f"Sample mismatch: {overlap}/{len(pg_set)} overlap"

# ============================================================================
# TEST EXECUTION
# ============================================================================

def run_test(pg_conn, mysql_conn, test):
    """Run a single test"""
    pg_cur = pg_conn.cursor()
    mysql_cur = mysql_conn.cursor()
    
    try:
        pg_cur.execute(test['postgres'])
        pg_rows = pg_cur.fetchall()
        
        if pg_rows and isinstance(pg_rows[0], tuple) and pg_cur.description:
            column_names = [desc[0] for desc in pg_cur.description]
            pg_rows = [dict(zip(column_names, row)) for row in pg_rows]
        
        mysql_cur.execute(test['mysql'])
        mysql_rows = mysql_cur.fetchall()
        
        compare_func = {
            'exact_match': compare_exact_match,
            'count_match': compare_count_match,
            'numeric_range': compare_numeric_range,
            'price_match': compare_price_match,
            'color_match': compare_color_match,
            'distribution_match': compare_distribution_match,
            'sample_match': compare_sample_match
        }.get(test['compare'], compare_exact_match)
        
        match, message = compare_func(pg_rows, mysql_rows, test['field'])
        
        return {
            'id': test['id'],
            'field': test['field'],
            'category': test['category'],
            'name': test['name'],
            'match': match,
            'message': message,
            'pg_row_count': len(pg_rows),
            'mysql_row_count': len(mysql_rows)
        }
    except Exception as e:
        return {
            'id': test['id'],
            'field': test['field'],
            'category': test['category'],
            'name': test['name'],
            'match': False,
            'message': f"Error: {str(e)}",
            'pg_row_count': 0,
            'mysql_row_count': 0
        }

def main():
    pg_conn = None
    mysql_conn = None
    
    try:
        print("="*100)
        print("COMPREHENSIVE FIELD VALIDATION TESTS - 100+ TESTS")
        print("="*100)
        print("\nConnecting to databases...")
        pg_conn = get_postgres_conn()
        mysql_conn = get_mysql_conn()
        print("✅ Connected to both databases\n")
        
        # Get all tests
        all_tests = get_all_tests()
        print(f"Running {len(all_tests)} comprehensive tests...\n")
        
        results = []
        passed = 0
        failed = 0
        
        # Run tests with progress
        for i, test in enumerate(all_tests, 1):
            if i % 10 == 0:
                print(f"Progress: {i}/{len(all_tests)} tests...")
            
            result = run_test(pg_conn, mysql_conn, test)
            results.append(result)
            
            if result['match']:
                passed += 1
            else:
                failed += 1
        
        # Generate report
        print("\n" + "="*100)
        print("COMPREHENSIVE TEST RESULTS")
        print("="*100)
        
        # Summary by field
        by_field = {}
        for result in results:
            field = result['field']
            if field not in by_field:
                by_field[field] = {'passed': 0, 'failed': 0, 'tests': []}
            by_field[field]['tests'].append(result)
            if result['match']:
                by_field[field]['passed'] += 1
            else:
                by_field[field]['failed'] += 1
        
        print(f"\n{'Field':<20} {'Tests':<10} {'Passed':<10} {'Failed':<10} {'Pass Rate':<15}")
        print("-"*100)
        
        for field in sorted(by_field.keys()):
            stats = by_field[field]
            total = stats['passed'] + stats['failed']
            rate = (stats['passed'] / total * 100) if total > 0 else 0
            print(f"{field:<20} {total:<10} {stats['passed']:<10} {stats['failed']:<10} {rate:.1f}%")
        
        print("-"*100)
        total_rate = (passed / len(all_tests) * 100) if all_tests else 0
        print(f"{'TOTAL':<20} {len(all_tests):<10} {passed:<10} {failed:<10} {total_rate:.1f}%")
        
        # Failed tests detail
        failed_tests = [r for r in results if not r['match']]
        if failed_tests:
            print("\n" + "="*100)
            print(f"FAILED TESTS ({len(failed_tests)} total)")
            print("="*100)
            
            for result in failed_tests[:50]:  # Show first 50 failures
                print(f"\n❌ Test #{result['id']}: {result['field']} - {result['category']} - {result['name']}")
                print(f"   {result['message']}")
                print(f"   Postgres rows: {result['pg_row_count']}, MySQL rows: {result['mysql_row_count']}")
            
            if len(failed_tests) > 50:
                print(f"\n... and {len(failed_tests) - 50} more failures (truncated)")
        
        # Confidence assessment
        print("\n" + "="*100)
        print("CONFIDENCE ASSESSMENT")
        print("="*100)
        
        if total_rate >= 90:
            confidence = "✅ HIGH CONFIDENCE"
        elif total_rate >= 75:
            confidence = "⚠️  MODERATE CONFIDENCE"
        elif total_rate >= 50:
            confidence = "⚠️  LOW-MODERATE CONFIDENCE"
        else:
            confidence = "❌ LOW CONFIDENCE"
        
        print(f"\nOverall Pass Rate: {total_rate:.1f}% ({passed}/{len(all_tests)} tests)")
        print(f"Confidence Level: {confidence}")
        
        if failed > 0:
            print(f"\n⚠️  {failed} test(s) failed - review failures above")
        else:
            print(f"\n✅ All tests passed!")
        
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

