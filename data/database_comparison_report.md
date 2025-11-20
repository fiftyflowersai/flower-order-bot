# Database Comparison Report

**Generated:** 2025-11-17T14:29:52.828071

**Databases:**
- Local: PostgreSQL (flower_bot_db)
- Live: MySQL (cms)

---

## Summary

- ✅ Matches: 0
- ⚠️  Differences: 26
- Total Comparisons: 26

---

## Detailed Comparisons

### ⚠️ total_products

**Description:** Total number of active products (base products, not color-expanded)

**Status:** DIFFERENT

**Postgres Query:**
```sql
SELECT COUNT(DISTINCT REGEXP_REPLACE(unique_id, '_color_\d+$', '')) FROM flowers
```

**MySQL Query:**
```sql
SELECT COUNT(*) FROM products WHERE status = 'active'
```

**Results:**
- Postgres: 1 rows
- MySQL: 1 rows

---

### ⚠️ total_variants

**Description:** Total number of active product variants

**Status:** DIFFERENT

**Postgres Query:**
```sql
SELECT COUNT(DISTINCT unique_id) FROM flowers
```

**MySQL Query:**
```sql
SELECT COUNT(*) FROM product_variants WHERE status = 'active'
```

**Results:**
- Postgres: 1 rows
- MySQL: 1 rows

---

### ⚠️ products_with_red

**Description:** Products with red color

**Status:** DIFFERENT

**Postgres Query:**
```sql
SELECT COUNT(*) FROM flowers WHERE has_red = true
```

**MySQL Query:**
```sql
SELECT COUNT(DISTINCT p.product_id) 
               FROM products p
               JOIN product_colors_link pcl ON p.product_id = pcl.product_id
               JOIN colors c ON pcl.color_id = c.color_id
               WHERE p.status = 'active'
                 AND c.status = 'active'
                 AND c.name IN ('Red', 'True Red', 'Wine Red', 'Cranberry', 'Burgundy', 'Rust')
```

**Results:**
- Postgres: 1 rows
- MySQL: 1 rows

---

### ⚠️ products_with_pink

**Description:** Products with pink color

**Status:** DIFFERENT

**Postgres Query:**
```sql
SELECT COUNT(*) FROM flowers WHERE has_pink = true
```

**MySQL Query:**
```sql
SELECT COUNT(DISTINCT p.product_id) 
               FROM products p
               JOIN product_colors_link pcl ON p.product_id = pcl.product_id
               JOIN colors c ON pcl.color_id = c.color_id
               WHERE p.status = 'active'
                 AND c.status = 'active'
                 AND c.name IN ('Pink', 'True Pink', 'Hot Pink', 'Dusty Pink', 'Light Pink', 'Blush', 'Dusty Rose', 'Mauve', 'Pinky Lavender', 'Fuchsia', 'Magenta', 'Coral')
```

**Results:**
- Postgres: 1 rows
- MySQL: 1 rows

---

### ⚠️ products_with_white

**Description:** Products with white color

**Status:** DIFFERENT

**Postgres Query:**
```sql
SELECT COUNT(*) FROM flowers WHERE has_white = true
```

**MySQL Query:**
```sql
SELECT COUNT(DISTINCT p.product_id) 
               FROM products p
               JOIN product_colors_link pcl ON p.product_id = pcl.product_id
               JOIN colors c ON pcl.color_id = c.color_id
               WHERE p.status = 'active'
                 AND c.status = 'active'
                 AND c.name IN ('White', 'Ivory', 'Natural', 'Champagne', 'Clear')
```

**Results:**
- Postgres: 1 rows
- MySQL: 1 rows

---

### ⚠️ products_with_yellow

**Description:** Products with yellow color

**Status:** DIFFERENT

**Postgres Query:**
```sql
SELECT COUNT(*) FROM flowers WHERE has_yellow = true
```

**MySQL Query:**
```sql
SELECT COUNT(DISTINCT p.product_id) 
               FROM products p
               JOIN product_colors_link pcl ON p.product_id = pcl.product_id
               JOIN colors c ON pcl.color_id = c.color_id
               WHERE p.status = 'active'
                 AND c.status = 'active'
                 AND c.name IN ('Yellow', 'Pale Yellow', 'Mustard Yellow', 'Dark Yellow', 'Amber', 'Chartreuse', 'Gold')
```

**Results:**
- Postgres: 1 rows
- MySQL: 1 rows

---

### ⚠️ products_with_orange

**Description:** Products with orange color

**Status:** DIFFERENT

**Postgres Query:**
```sql
SELECT COUNT(*) FROM flowers WHERE has_orange = true
```

**MySQL Query:**
```sql
SELECT COUNT(DISTINCT p.product_id) 
               FROM products p
               JOIN product_colors_link pcl ON p.product_id = pcl.product_id
               JOIN colors c ON pcl.color_id = c.color_id
               WHERE p.status = 'active'
                 AND c.status = 'active'
                 AND c.name IN ('Orange', 'Peach', 'Sunset', 'Terracotta', 'Copper', 'Dark Orange', 'True Orange')
```

**Results:**
- Postgres: 1 rows
- MySQL: 1 rows

---

### ⚠️ products_with_purple

**Description:** Products with purple color

**Status:** DIFFERENT

**Postgres Query:**
```sql
SELECT COUNT(*) FROM flowers WHERE has_purple = true
```

**MySQL Query:**
```sql
SELECT COUNT(DISTINCT p.product_id) 
               FROM products p
               JOIN product_colors_link pcl ON p.product_id = pcl.product_id
               JOIN colors c ON pcl.color_id = c.color_id
               WHERE p.status = 'active'
                 AND c.status = 'active'
                 AND c.name IN ('Purple', 'Lavender', 'Pinky Lavender', 'True Purple', 'Dark Purple')
```

**Results:**
- Postgres: 1 rows
- MySQL: 1 rows

---

### ⚠️ products_with_blue

**Description:** Products with blue color

**Status:** DIFFERENT

**Postgres Query:**
```sql
SELECT COUNT(*) FROM flowers WHERE has_blue = true
```

**MySQL Query:**
```sql
SELECT COUNT(DISTINCT p.product_id) 
               FROM products p
               JOIN product_colors_link pcl ON p.product_id = pcl.product_id
               JOIN colors c ON pcl.color_id = c.color_id
               WHERE p.status = 'active'
                 AND c.status = 'active'
                 AND c.name IN ('Blue', 'Soft Blue', 'Light Blue', 'Teal')
```

**Results:**
- Postgres: 1 rows
- MySQL: 1 rows

---

### ⚠️ products_with_green

**Description:** Products with green color

**Status:** DIFFERENT

**Postgres Query:**
```sql
SELECT COUNT(*) FROM flowers WHERE has_green = true
```

**MySQL Query:**
```sql
SELECT COUNT(DISTINCT p.product_id) 
               FROM products p
               JOIN product_colors_link pcl ON p.product_id = pcl.product_id
               JOIN colors c ON pcl.color_id = c.color_id
               WHERE p.status = 'active'
                 AND c.status = 'active'
                 AND c.name IN ('Green', 'Sage Green', 'Emerald Green', 'Forest Green', 'Lime Green', 'Light Green', 'True Green')
```

**Results:**
- Postgres: 1 rows
- MySQL: 1 rows

---

### ⚠️ products_without_colors

**Description:** Products without any color assigned

**Status:** DIFFERENT

**Postgres Query:**
```sql
SELECT COUNT(*) FROM flowers WHERE NOT (has_red OR has_pink OR has_white OR has_yellow OR has_orange OR has_purple OR has_blue OR has_green)
```

**MySQL Query:**
```sql
SELECT COUNT(DISTINCT p.product_id)
           FROM products p
           LEFT JOIN product_colors_link pcl ON p.product_id = pcl.product_id
           WHERE p.status = 'active'
             AND pcl.product_id IS NULL
```

**Results:**
- Postgres: 1 rows
- MySQL: 1 rows

---

### ⚠️ ready_to_go_products

**Description:** Products with 'Ready To Go' effort level

**Status:** DIFFERENT

**Postgres Query:**
```sql
SELECT COUNT(*) FROM flowers WHERE diy_level = 'Ready To Go'
```

**MySQL Query:**
```sql
SELECT COUNT(DISTINCT pav.product_id)
           FROM product_attribute_values pav
           JOIN products p ON pav.product_id = p.product_id
           WHERE pav.attribute_id = 370
             AND p.status = 'active'
             AND LOWER(pav.value) LIKE '%ready to go%'
```

**Results:**
- Postgres: 1 rows
- MySQL: 1 rows

---

### ⚠️ diy_in_kit_products

**Description:** Products with 'DIY In A Kit' effort level

**Status:** DIFFERENT

**Postgres Query:**
```sql
SELECT COUNT(*) FROM flowers WHERE diy_level = 'DIY In A Kit'
```

**MySQL Query:**
```sql
SELECT COUNT(DISTINCT pav.product_id)
           FROM product_attribute_values pav
           JOIN products p ON pav.product_id = p.product_id
           WHERE pav.attribute_id = 370
             AND p.status = 'active'
             AND LOWER(pav.value) LIKE '%diy in a kit%'
```

**Results:**
- Postgres: 1 rows
- MySQL: 1 rows

---

### ⚠️ diy_from_scratch_products

**Description:** Products with 'DIY From Scratch' effort level

**Status:** DIFFERENT

**Postgres Query:**
```sql
SELECT COUNT(*) FROM flowers WHERE diy_level = 'DIY From Scratch'
```

**MySQL Query:**
```sql
SELECT COUNT(DISTINCT pav.product_id)
           FROM product_attribute_values pav
           JOIN products p ON pav.product_id = p.product_id
           WHERE pav.attribute_id = 370
             AND p.status = 'active'
             AND LOWER(pav.value) LIKE '%diy from scratch%'
```

**Results:**
- Postgres: 1 rows
- MySQL: 1 rows

---

### ⚠️ products_without_diy_level

**Description:** Products without DIY level assigned

**Status:** DIFFERENT

**Postgres Query:**
```sql
SELECT COUNT(*) FROM flowers WHERE diy_level IS NULL
```

**MySQL Query:**
```sql
SELECT COUNT(DISTINCT p.product_id)
           FROM products p
           LEFT JOIN product_attribute_values pav ON p.product_id = pav.product_id AND pav.attribute_id = 370
           WHERE p.status = 'active'
             AND pav.product_id IS NULL
```

**Results:**
- Postgres: 1 rows
- MySQL: 1 rows

---

### ⚠️ wedding_products

**Description:** Products tagged for weddings

**Status:** DIFFERENT

**Postgres Query:**
```sql
SELECT COUNT(*) FROM flowers WHERE LOWER(holiday_occasion) LIKE '%wedding%'
```

**MySQL Query:**
```sql
SELECT COUNT(DISTINCT pav.product_id)
           FROM product_attribute_values pav
           JOIN products p ON pav.product_id = p.product_id
           WHERE pav.attribute_id = 374
             AND p.status = 'active'
             AND LOWER(pav.value) LIKE '%wedding%'
```

**Results:**
- Postgres: 1 rows
- MySQL: 1 rows

---

### ⚠️ products_with_occasions

**Description:** Products with occasion tags

**Status:** DIFFERENT

**Postgres Query:**
```sql
SELECT COUNT(*) FROM flowers WHERE holiday_occasion IS NOT NULL
```

**MySQL Query:**
```sql
SELECT COUNT(DISTINCT pav.product_id)
           FROM product_attribute_values pav
           JOIN products p ON pav.product_id = p.product_id
           WHERE pav.attribute_id = 374
             AND p.status = 'active'
             AND pav.value IS NOT NULL
             AND pav.value != ''
```

**Results:**
- Postgres: 1 rows
- MySQL: 1 rows

---

### ⚠️ products_without_occasions

**Description:** Products without occasion tags

**Status:** DIFFERENT

**Postgres Query:**
```sql
SELECT COUNT(*) FROM flowers WHERE holiday_occasion IS NULL
```

**MySQL Query:**
```sql
SELECT COUNT(DISTINCT p.product_id)
           FROM products p
           LEFT JOIN product_attribute_values pav ON p.product_id = pav.product_id AND pav.attribute_id = 374
           WHERE p.status = 'active'
             AND pav.product_id IS NULL
```

**Results:**
- Postgres: 1 rows
- MySQL: 1 rows

---

### ⚠️ year_round_products

**Description:** Products available year-round

**Status:** DIFFERENT

**Postgres Query:**
```sql
SELECT COUNT(*) FROM flowers WHERE is_year_round = true
```

**MySQL Query:**
```sql
SELECT COUNT(DISTINCT p.product_id)
           FROM products p
           JOIN product_availability pa ON p.product_id = pa.product_id
           WHERE p.status = 'active'
             AND JSON_EXTRACT(pa.available_dates, '$[0].start_month') = 1
             AND JSON_EXTRACT(pa.available_dates, '$[0].start_day') = 1
             AND JSON_EXTRACT(pa.available_dates, '$[0].end_month') = 12
             AND JSON_EXTRACT(pa.available_dates, '$[0].end_day') = 31
```

**Results:**
- Postgres: 1 rows
- MySQL: 1 rows

---

### ⚠️ seasonal_products

**Description:** Products with seasonal availability (not year-round)

**Status:** DIFFERENT

**Postgres Query:**
```sql
SELECT COUNT(*) FROM flowers WHERE is_year_round = false
```

**MySQL Query:**
```sql
SELECT COUNT(DISTINCT p.product_id)
           FROM products p
           JOIN product_availability pa ON p.product_id = pa.product_id
           WHERE p.status = 'active'
             AND NOT (
               JSON_EXTRACT(pa.available_dates, '$[0].start_month') = 1
               AND JSON_EXTRACT(pa.available_dates, '$[0].start_day') = 1
               AND JSON_EXTRACT(pa.available_dates, '$[0].end_month') = 12
               AND JSON_EXTRACT(pa.available_dates, '$[0].end_day') = 31
             )
```

**Results:**
- Postgres: 1 rows
- MySQL: 1 rows

---

### ⚠️ multi_range_seasonal_products

**Description:** Products with multiple availability ranges

**Status:** DIFFERENT

**Postgres Query:**
```sql
SELECT COUNT(*) FROM flowers WHERE season_range_2_start_month IS NOT NULL
```

**MySQL Query:**
```sql
SELECT 0
```

**Results:**
- Postgres: 1 rows
- MySQL: 1 rows

---

### ⚠️ avg_price

**Description:** Average product price

**Status:** DIFFERENT

**Postgres Query:**
```sql
SELECT AVG(variant_price)::numeric(10,2) FROM flowers WHERE variant_price IS NOT NULL
```

**MySQL Query:**
```sql
SELECT AVG(price) FROM product_variants WHERE status = 'active' AND price IS NOT NULL
```

**Results:**
- Postgres: 1 rows
- MySQL: 1 rows

---

### ⚠️ min_price

**Description:** Minimum product price

**Status:** DIFFERENT

**Postgres Query:**
```sql
SELECT MIN(variant_price) FROM flowers WHERE variant_price IS NOT NULL
```

**MySQL Query:**
```sql
SELECT MIN(price) FROM product_variants WHERE status = 'active' AND price IS NOT NULL
```

**Results:**
- Postgres: 1 rows
- MySQL: 1 rows

---

### ⚠️ max_price

**Description:** Maximum product price

**Status:** DIFFERENT

**Postgres Query:**
```sql
SELECT MAX(variant_price) FROM flowers WHERE variant_price IS NOT NULL
```

**MySQL Query:**
```sql
SELECT MAX(price) FROM product_variants WHERE status = 'active' AND price IS NOT NULL
```

**Results:**
- Postgres: 1 rows
- MySQL: 1 rows

---

### ⚠️ products_under_100

**Description:** Products priced under $100

**Status:** DIFFERENT

**Postgres Query:**
```sql
SELECT COUNT(*) FROM flowers WHERE variant_price < 100
```

**MySQL Query:**
```sql
SELECT COUNT(*) FROM product_variants WHERE status = 'active' AND price < 100
```

**Results:**
- Postgres: 1 rows
- MySQL: 1 rows

---

### ⚠️ sample_product_names

**Description:** Sample product names (first 10 alphabetically)

**Status:** DIFFERENT

**Postgres Query:**
```sql
SELECT DISTINCT product_name FROM flowers ORDER BY product_name LIMIT 10
```

**MySQL Query:**
```sql
SELECT name FROM products WHERE status = 'active' ORDER BY name LIMIT 10
```

**Results:**
- Postgres: 10 rows
- MySQL: 10 rows

---

