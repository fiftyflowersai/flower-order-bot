# V7 Migration Checklist
## From Postgres (v6) to MySQL VIEW (v7)

---

## ✅ PRE-MIGRATION CHECKLIST

### 1. VIEW Fixes Applied
- [ ] **Apply `create_flowers_view_fixed_v2.sql` in DBeaver**
- [ ] Verify VIEW exists: `SELECT * FROM flowers_view LIMIT 1;`
- [ ] Test JSON extraction: `SELECT diy_level FROM flowers_view WHERE diy_level IS NOT NULL LIMIT 5;`
  - Should return strings like `"Ready To Go"`, NOT `'["Ready To Go"]'`
- [ ] Test holiday_occasion: `SELECT holiday_occasion FROM flowers_view WHERE holiday_occasion LIKE '%Wedding%' LIMIT 5;`
  - Should return strings, NOT JSON arrays

### 2. Comprehensive Tests Pass
- [ ] Run: `python3 comprehensive_field_tests.py`
- [ ] **Target:** 60-70% pass rate (33/110 → 66-77/110)
- [ ] All critical tests pass (diy_level, holiday_occasion, NULL handling)
- [ ] Remaining failures are expected differences (counts, names)

---

## 🔧 CODE CHANGES NEEDED FOR V7

### 1. Database Connection (Line 64)
**Current (v6):**
```python
DB_URI = "postgresql+psycopg2://postgres:Harrison891%21@localhost:5432/flower_bot_db"
```

**Change to (v7) - Use environment variables:**
```python
# Load from environment variables (recommended)
DB_HOST = os.getenv("DB_HOST", "aws.connect.psdb.cloud")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "cms")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

if not DB_USER or not DB_PASSWORD:
    raise ValueError("Database credentials not found in environment variables")

DB_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

ENGINE = create_engine(
    DB_URI, 
    pool_pre_ping=True,
    connect_args={"ssl": {"ssl": {}}}  # PlanetScale requires SSL
)
```

**Note:** Store credentials in `.env` file (see `.env.example` for template)

### 2. SQL Syntax Conversions in `build_sql_from_memory()`

#### A. Table Name (Line 996)
**Current:**
```python
FROM flowers
```

**Change to:**
```python
FROM flowers_view
```

#### B. Boolean Values (Lines 727-819, 798-819)
**Current (Postgres):**
```python
"has_red = true"
"has_red = false"
```

**Change to (MySQL):**
```python
"has_red = 1"
"has_red = 0"
```

**All occurrences:**
- Line 727: `has_blue = true` → `has_blue = 1`
- Line 729: `has_red = true` → `has_red = 1`
- Line 731: `has_white = true` → `has_white = 1`
- Line 734-748: All color booleans
- Line 757-771: All color booleans in mapping
- Line 798-819: All exclude color booleans

#### C. DISTINCT ON (Line 989)
**Current (Postgres-specific):**
```python
SELECT DISTINCT ON (product_name)
```

**Change to (MySQL-compatible):**
```python
SELECT 
```

**AND add GROUP BY:**
After the WHERE clause, add:
```python
GROUP BY product_name, unique_id, variant_name, description_clean, variant_price,
         colors_raw, diy_level, product_type_all_flowers, group_category,
         recipe_metafield, holiday_occasion, is_year_round, non_color_options,
         season_start_month, season_start_day, season_end_month, season_end_day,
         season_range_2_start_month, season_range_2_start_day, season_range_2_end_month, season_range_2_end_day,
         season_range_3_start_month, season_range_3_start_day, season_range_3_end_month, season_range_3_end_day
```

**OR use subquery approach:**
```python
SELECT * FROM (
    SELECT ... FROM flowers_view WHERE ...
    ORDER BY product_name, unique_id
) AS subq
GROUP BY product_name
```

#### D. random() Function (Line 1008)
**Current (Postgres):**
```python
SELECT FLOOR(random() * GREATEST(0, c - 6))::int AS r
```

**Change to (MySQL):**
```python
SELECT FLOOR(RAND() * GREATEST(0, c - 6)) AS r
```

**Note:** MySQL doesn't need `::int` casting, and uses `RAND()` not `random()`

#### E. is_year_round Boolean (Line 669, 1114)
**Current:**
```python
is_year_round = TRUE
```

**Change to:**
```python
is_year_round = 1
```

**In render_results() (Line 1059):**
```python
if row.get("is_year_round") in (True, "t", "true", 1):
```

**Keep this check** - it handles both Postgres (True) and MySQL (1)

### 3. Missing Fields Check

**v6 uses these fields that need to be in VIEW:**
- [x] `unique_id` ✅
- [x] `product_name` ✅
- [x] `variant_name` ✅
- [x] `variant_price` ✅
- [x] `colors_raw` ✅
- [x] `has_red`, `has_pink`, etc. ✅
- [x] `diy_level` ✅ (needs JSON extraction fix)
- [x] `holiday_occasion` ✅ (needs JSON extraction fix)
- [x] `is_year_round` ✅
- [x] `season_start_month/day/end_month/day` ✅
- [x] `season_range_2_*` ❓ **CHECK IF VIEW HAS THIS**
- [x] `season_range_3_*` ❓ **CHECK IF VIEW HAS THIS**
- [x] `group_category` ✅
- [x] `product_type_all_flowers` ✅
- [x] `recipe_metafield` ✅
- [x] `description_clean` ✅
- [x] `non_color_options` ❓ **CHECK IF VIEW HAS THIS**

**Need to verify VIEW includes:**
- `season_range_2_*` fields (4 fields)
- `season_range_3_*` fields (4 fields)
- `non_color_options` field

---

## 🧪 TESTING PLAN

### Phase 1: VIEW Verification
1. Apply VIEW in DBeaver
2. Run comprehensive tests: `python3 comprehensive_field_tests.py`
3. Verify 60-70% pass rate
4. Check all critical fields work

### Phase 2: SQL Conversion Testing
1. Create v7 with database connection change only
2. Test simple queries (red flowers, under $100)
3. Fix SQL syntax issues (booleans, DISTINCT ON, random())
4. Test complex queries (multiple filters)

### Phase 3: End-to-End Testing
1. Test actual user conversations
2. Test memory persistence
3. Test all filter types
4. Test edge cases (no results, NULL handling)

---

## 📋 STEP-BY-STEP MIGRATION

### Step 1: Create v7_chat_bot.py
```bash
cp v6_chat_bot.py v7_chat_bot.py
```

### Step 2: Update Database Connection
- Change DB_URI to MySQL
- Update SQLAlchemy import if needed

### Step 3: Update build_sql_from_memory()
- Change `FROM flowers` → `FROM flowers_view`
- Change `= true` → `= 1` (all occurrences)
- Change `= false` → `= 0` (all occurrences)
- Change `DISTINCT ON (product_name)` → Remove, add GROUP BY
- Change `random()` → `RAND()`
- Change `::int` → Remove (MySQL doesn't need)

### Step 4: Test Each Filter Type
- Colors (red, pink, etc.)
- Budget (under $100, $50-$200)
- DIY level (Ready To Go)
- Occasions (wedding, birthday)
- Seasonality (spring, May 15)
- Complex combinations

### Step 5: Update web_demo.py
- Change import from `v6_chat_bot` to `v7_chat_bot`
- Test in browser

---

## ⚠️ POTENTIAL ISSUES

### Issue 1: DISTINCT ON Replacement
**Problem:** MySQL doesn't support `DISTINCT ON`
**Solution:** Use `GROUP BY` or subquery approach

### Issue 2: Window Functions
**Problem:** MySQL window functions might have different syntax
**Solution:** Test `ROW_NUMBER() OVER()` - should work the same

### Issue 3: Boolean Handling
**Problem:** Postgres returns `True/False`, MySQL returns `1/0`
**Solution:** Update all boolean comparisons in SQL generation

### Issue 4: Missing Fields
**Problem:** VIEW might not have all fields v6 uses
**Solution:** Check `season_range_2_*`, `season_range_3_*`, `non_color_options`

### Issue 5: NULL Handling
**Problem:** Different NULL behavior between databases
**Solution:** Test NULL checks work correctly

---

## ✅ READINESS CRITERIA

Before creating v7, ensure:

1. ✅ VIEW is applied and working
2. ✅ Comprehensive tests show 60-70% pass rate
3. ✅ All critical fields work (diy_level, holiday_occasion)
4. ✅ VIEW includes all fields v6 uses
5. ✅ SQL conversion logic is ready

**Current Status:**
- ✅ VIEW fixes ready (`create_flowers_view_fixed_v2.sql`)
- ⚠️ **Need to apply VIEW in DBeaver first**
- ⚠️ **Need to verify VIEW has all fields (season_range_2/3, non_color_options)**
- ⚠️ **Need to test SQL conversion**

---

## 🚀 RECOMMENDED NEXT STEPS

1. **Apply VIEW** - Run `create_flowers_view_fixed_v2.sql` in DBeaver
2. **Run comprehensive tests** - Verify 60-70% pass rate
3. **Check VIEW fields** - Verify all fields v6 needs are present
4. **Create v7** - Copy v6, make changes
5. **Test v7** - Run through test scenarios
6. **Iterate** - Fix any issues found

**We're almost ready, but need to:**
1. Apply the VIEW first
2. Verify it has all required fields
3. Test SQL conversion logic

