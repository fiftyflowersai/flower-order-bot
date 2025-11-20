# VIEW Changes: v1 → v2 (Fixed)

## Summary of All Changes

Comparing `create_flowers_view_v1.sql` (original) with `create_flowers_view_fixed_v2.sql` (fixed version).

---

## 🔧 CHANGE 1: CREATE OR REPLACE

**v1:**
```sql
CREATE VIEW flowers_view AS
```

**v2:**
```sql
CREATE OR REPLACE VIEW flowers_view AS
```

**Why:** Allows updating the VIEW without dropping it first.

---

## 🔧 CHANGE 2: Seasonality Date Fields - Remove COALESCE Defaults

**v1 (Lines 46-49):**
```sql
COALESCE(JSON_EXTRACT(pa.available_dates, '$[0].start_month'), 1) AS season_start_month,
COALESCE(JSON_EXTRACT(pa.available_dates, '$[0].start_day'), 1) AS season_start_day,
COALESCE(JSON_EXTRACT(pa.available_dates, '$[0].end_month'), 12) AS season_end_month,
COALESCE(JSON_EXTRACT(pa.available_dates, '$[0].end_day'), 31) AS season_end_day,
```

**v2 (Lines 50-53):**
```sql
JSON_EXTRACT(pa.available_dates, '$[0].start_month') AS season_start_month,
JSON_EXTRACT(pa.available_dates, '$[0].start_day') AS season_start_day,
JSON_EXTRACT(pa.available_dates, '$[0].end_month') AS season_end_month,
JSON_EXTRACT(pa.available_dates, '$[0].end_day') AS season_end_day,
```

**Why:** 
- **Problem:** COALESCE was defaulting NULL dates to `1/1` and `12/31`, incorrectly marking products as year-round
- **Fix:** Remove COALESCE to allow NULL values when no seasonality data exists
- **Impact:** Products without availability data now correctly show NULL instead of being marked as year-round

---

## 🔧 CHANGE 3: Add Seasonality Range 2 & 3 Fields

**v1:** ❌ Not included

**v2 (Lines 56-65):**
```sql
-- Seasonality Range 2 (for products with multiple availability ranges)
JSON_EXTRACT(pa.available_dates, '$[1].start_month') AS season_range_2_start_month,
JSON_EXTRACT(pa.available_dates, '$[1].start_day') AS season_range_2_start_day,
JSON_EXTRACT(pa.available_dates, '$[1].end_month') AS season_range_2_end_month,
JSON_EXTRACT(pa.available_dates, '$[1].end_day') AS season_range_2_end_day,

-- Seasonality Range 3 (for products with three availability ranges)
JSON_EXTRACT(pa.available_dates, '$[2].start_month') AS season_range_3_start_month,
JSON_EXTRACT(pa.available_dates, '$[2].start_day') AS season_range_3_start_day,
JSON_EXTRACT(pa.available_dates, '$[2].end_month') AS season_range_3_end_month,
JSON_EXTRACT(pa.available_dates, '$[2].end_day') AS season_range_3_end_day,
```

**Why:**
- **Problem:** v6_chat_bot.py uses `season_range_2_*` and `season_range_3_*` fields for products with multiple availability periods
- **Fix:** Extract ranges 2 and 3 from the `available_dates` JSON array
- **Impact:** Products with multiple seasonal periods (e.g., spring AND fall) now work correctly

---

## 🔧 CHANGE 4: is_year_round - Don't Default NULL to TRUE

**v1 (Lines 50-58):**
```sql
CASE
  WHEN JSON_EXTRACT(pa.available_dates, '$[0].start_month') = 1
   AND JSON_EXTRACT(pa.available_dates, '$[0].start_day') = 1
   AND JSON_EXTRACT(pa.available_dates, '$[0].end_month') = 12
   AND JSON_EXTRACT(pa.available_dates, '$[0].end_day') = 31
  THEN TRUE
  WHEN pa.available_dates IS NULL THEN TRUE  -- ❌ BUG: Defaults NULL to TRUE
  ELSE FALSE
END AS is_year_round,
```

**v2 (Lines 68-76):**
```sql
CASE
  WHEN JSON_EXTRACT(pa.available_dates, '$[0].start_month') = 1
   AND JSON_EXTRACT(pa.available_dates, '$[0].start_day') = 1
   AND JSON_EXTRACT(pa.available_dates, '$[0].end_month') = 12
   AND JSON_EXTRACT(pa.available_dates, '$[0].end_day') = 31
  THEN TRUE
  WHEN pa.available_dates IS NULL THEN NULL  -- ✅ FIX: NULL stays NULL
  ELSE FALSE
END AS is_year_round,
```

**Why:**
- **Problem:** Products without availability data were incorrectly marked as year-round
- **Fix:** Return NULL when `available_dates` is NULL (unknown availability)
- **Impact:** Products with no availability data now correctly show NULL instead of being marked as year-round

---

## 🔧 CHANGE 5: seasonality - Extract from JSON Array

**v1 (Line 60):**
```sql
(SELECT pav.value FROM product_attribute_values pav
 WHERE pav.product_id = p.product_id AND pav.attribute_id = 56 LIMIT 1) AS seasonality,
```

**v2 (Lines 78-90):**
```sql
(SELECT 
   CASE 
     WHEN JSON_TYPE(pav.value) = 'ARRAY' AND JSON_LENGTH(pav.value) > 1 THEN
       (SELECT GROUP_CONCAT(JSON_UNQUOTE(JSON_EXTRACT(pav.value, CONCAT('$[', idx, ']'))) SEPARATOR '; ')
        FROM (SELECT 0 as idx UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) indices
        WHERE JSON_EXTRACT(pav.value, CONCAT('$[', idx, ']')) IS NOT NULL)
     WHEN JSON_TYPE(pav.value) = 'ARRAY' AND JSON_LENGTH(pav.value) = 1 THEN
       JSON_UNQUOTE(JSON_EXTRACT(pav.value, '$[0]'))
     ELSE pav.value
   END
 FROM product_attribute_values pav
 WHERE pav.product_id = p.product_id AND pav.attribute_id = 56 LIMIT 1) AS seasonality,
```

**Why:**
- **Problem:** `pav.value` stores JSON arrays like `["Spring", "Summer"]` instead of plain strings
- **Fix:** Extract first element from array, or join multiple values with semicolon
- **Impact:** Queries like `WHERE seasonality LIKE '%Spring%'` now work correctly

---

## 🔧 CHANGE 6: diy_level - Extract from JSON Array

**v1 (Lines 62-63):**
```sql
(SELECT pav.value FROM product_attribute_values pav
 WHERE pav.product_id = p.product_id AND pav.attribute_id = 370 LIMIT 1) AS diy_level,
```

**v2 (Lines 92-102):**
```sql
(SELECT 
   CASE 
     WHEN JSON_TYPE(pav.value) = 'ARRAY' AND JSON_LENGTH(pav.value) > 0 THEN
       JSON_UNQUOTE(JSON_EXTRACT(pav.value, '$[0]'))
     WHEN JSON_TYPE(pav.value) = 'ARRAY' AND JSON_LENGTH(pav.value) = 0 THEN
       NULL
     ELSE pav.value
   END
 FROM product_attribute_values pav
 WHERE pav.product_id = p.product_id AND pav.attribute_id = 370 LIMIT 1) AS diy_level,
```

**Why:**
- **Problem:** `pav.value` stores JSON arrays like `["Ready To Go"]` instead of plain strings
- **Fix:** Extract first element from array, handle empty arrays as NULL
- **Impact:** Queries like `WHERE diy_level = 'Ready To Go'` now work (was returning 0 results before)

---

## 🔧 CHANGE 7: holiday_occasion - Extract from JSON Array

**v1 (Lines 64-65):**
```sql
(SELECT pav.value FROM product_attribute_values pav
 WHERE pav.product_id = p.product_id AND pav.attribute_id = 374 LIMIT 1) AS holiday_occasion,
```

**v2 (Lines 104-116):**
```sql
(SELECT 
   CASE 
     WHEN JSON_TYPE(pav.value) = 'ARRAY' AND JSON_LENGTH(pav.value) > 1 THEN
       (SELECT GROUP_CONCAT(JSON_UNQUOTE(JSON_EXTRACT(pav.value, CONCAT('$[', idx, ']'))) SEPARATOR '; ')
        FROM (SELECT 0 as idx UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) indices
        WHERE JSON_EXTRACT(pav.value, CONCAT('$[', idx, ']')) IS NOT NULL)
     WHEN JSON_TYPE(pav.value) = 'ARRAY' AND JSON_LENGTH(pav.value) = 1 THEN
       JSON_UNQUOTE(JSON_EXTRACT(pav.value, '$[0]'))
     ELSE pav.value
   END
 FROM product_attribute_values pav
 WHERE pav.product_id = p.product_id AND pav.attribute_id = 374 LIMIT 1) AS holiday_occasion,
```

**Why:**
- **Problem:** `pav.value` stores JSON arrays like `["Wedding", "Birthday"]` instead of plain strings
- **Fix:** Extract first element from array, or join multiple values with semicolon
- **Impact:** Queries like `WHERE holiday_occasion LIKE '%Wedding%'` now work correctly

---

## 🔧 CHANGE 8: product_type_all_flowers - Extract from JSON Array

**v1 (Lines 66-67):**
```sql
(SELECT pav.value FROM product_attribute_values pav
 WHERE pav.product_id = p.product_id AND pav.attribute_id = 371 LIMIT 1) AS product_type_all_flowers,
```

**v2 (Lines 118-128):**
```sql
(SELECT 
   CASE 
     WHEN JSON_TYPE(pav.value) = 'ARRAY' AND JSON_LENGTH(pav.value) > 0 THEN
       JSON_UNQUOTE(JSON_EXTRACT(pav.value, '$[0]'))
     WHEN JSON_TYPE(pav.value) = 'ARRAY' AND JSON_LENGTH(pav.value) = 0 THEN
       NULL
     ELSE pav.value
   END
 FROM product_attribute_values pav
 WHERE pav.product_id = p.product_id AND pav.attribute_id = 371 LIMIT 1) AS product_type_all_flowers,
```

**Why:**
- **Problem:** `pav.value` stores JSON arrays like `["Bouquet"]` instead of plain strings
- **Fix:** Extract first element from array, handle empty arrays as NULL
- **Impact:** Queries using `product_type_all_flowers` now work correctly

---

## 🔧 CHANGE 9: group_category - Extract from JSON Array

**v1 (Lines 70-71):**
```sql
(SELECT pav.value FROM product_attribute_values pav
 WHERE pav.product_id = p.product_id AND pav.attribute_id = 365 LIMIT 1) AS group_category
```

**v2 (Lines 139-149):**
```sql
(SELECT 
   CASE 
     WHEN JSON_TYPE(pav.value) = 'ARRAY' AND JSON_LENGTH(pav.value) > 0 THEN
       JSON_UNQUOTE(JSON_EXTRACT(pav.value, '$[0]'))
     WHEN JSON_TYPE(pav.value) = 'ARRAY' AND JSON_LENGTH(pav.value) = 0 THEN
       NULL
     ELSE pav.value
   END
 FROM product_attribute_values pav
 WHERE pav.product_id = p.product_id AND pav.attribute_id = 365 LIMIT 1) AS group_category
```

**Why:**
- **Problem:** `pav.value` stores JSON arrays like `["Roses"]` instead of plain strings
- **Fix:** Extract first element from array, handle empty arrays as NULL
- **Impact:** Queries using `group_category` now work correctly

---

## 🔧 CHANGE 10: Add non_color_options Field

**v1:** ❌ Not included

**v2 (Lines 134-137):**
```sql
-- non_color_options (aggregated from variant_options - complex, set to NULL for now)
-- Note: This field is only used for display, not in WHERE clauses
-- Can be enhanced later to aggregate from variant_options table
NULL AS non_color_options,
```

**Why:**
- **Problem:** v6_chat_bot.py expects this field (used for display only, not in WHERE clauses)
- **Fix:** Add field, set to NULL for now (can be enhanced later to aggregate from `variant_options` table)
- **Impact:** v7 won't error when accessing this field (though it will be NULL)

---

## 📊 Summary Table

| Field | v1 Behavior | v2 Behavior | Impact |
|-------|-------------|--------------|--------|
| **season_start_month/day** | COALESCE defaults to 1/1 | NULL when missing | ✅ Correct NULL handling |
| **season_end_month/day** | COALESCE defaults to 12/31 | NULL when missing | ✅ Correct NULL handling |
| **season_range_2_*** | ❌ Missing | ✅ Added | ✅ Multi-range products work |
| **season_range_3_*** | ❌ Missing | ✅ Added | ✅ Multi-range products work |
| **is_year_round** | NULL → TRUE (wrong) | NULL → NULL (correct) | ✅ Correct NULL handling |
| **seasonality** | Returns JSON array | Extracts string(s) | ✅ Queries work |
| **diy_level** | Returns JSON array | Extracts string | ✅ Queries work |
| **holiday_occasion** | Returns JSON array | Extracts string(s) | ✅ Queries work |
| **product_type_all_flowers** | Returns JSON array | Extracts string | ✅ Queries work |
| **group_category** | Returns JSON array | Extracts string | ✅ Queries work |
| **non_color_options** | ❌ Missing | ✅ Added (NULL) | ✅ No errors |

---

## 🎯 Critical Fixes

### 1. JSON Array Extraction (5 fields)
**Fields:** `diy_level`, `holiday_occasion`, `seasonality`, `product_type_all_flowers`, `group_category`

**Problem:** All returned JSON arrays like `["Ready To Go"]` instead of strings like `"Ready To Go"`

**Impact:** Queries like `WHERE diy_level = 'Ready To Go'` returned 0 results

**Fix:** Extract first element from JSON array, handle multiple values and empty arrays

### 2. Seasonality NULL Handling (2 issues)
**Problem 1:** COALESCE defaulted NULL dates to `1/1` and `12/31`
**Problem 2:** `is_year_round` defaulted NULL to TRUE

**Impact:** Products without availability data were incorrectly marked as year-round

**Fix:** Remove COALESCE defaults, allow NULL values

### 3. Missing Fields (9 fields)
**Problem:** `season_range_2_*`, `season_range_3_*`, and `non_color_options` were missing

**Impact:** v6 queries using these fields would fail

**Fix:** Add all missing fields

---

## ✅ Result

**v1:** 25 fields, JSON arrays not extracted, NULL defaults incorrect
**v2:** 34 fields, JSON arrays extracted, NULL handling correct

**Test Pass Rate:**
- **v1:** ~33.6% (37/110 tests)
- **v2 (expected):** 60-70% (66-77/110 tests)

**Critical Fixes:** All JSON array extraction and NULL handling issues resolved!

