# V7 Testing Guide

## Quick Start

### 1. Test the Chatbot Directly
```bash
python3 test_v7_iterative.py
```

This will run 8 test queries and show you which ones pass/fail.

### 2. Test the Web API

**Start the server:**
```bash
python3 web_demo_v2.py
```

**In another terminal, test with curl:**
```bash
# Simple test
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "red flowers", "session_id": "test"}'

# Complex test
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "red roses for a wedding", "session_id": "test"}'
```

---

## Known Issues & Fixes Applied

### ✅ Fixed: Result Format Handling
**Issue:** `'str' object has no attribute 'get'`

**Fix Applied:** Updated `run_sql()` function to handle MySQL result format:
- Added multiple fallback methods for converting rows to dictionaries
- Handles SQLAlchemy Row objects, tuples, and dictionaries
- Better error handling

### ⚠️ Potential Issues to Watch For

1. **Window Functions (ROW_NUMBER, COUNT OVER)**
   - MySQL 8.0+ supports window functions
   - If using older MySQL, may need alternative approach

2. **GROUP BY with Many Columns**
   - MySQL requires all non-aggregated columns in GROUP BY
   - We've included all columns, should work

3. **Boolean Values**
   - MySQL uses 1/0 instead of true/false
   - All conversions applied

---

## Test Queries

### Basic Filters
- `"red flowers"` - Color filter
- `"under $100"` - Budget filter
- `"ready to go flowers"` - DIY level
- `"wedding flowers"` - Occasion

### Complex Filters
- `"red roses for a wedding"` - Color + flower type + occasion
- `"red and white flowers under $200"` - Multiple colors + budget
- `"pink flowers for valentine's day"` - Color + occasion

### Edge Cases
- `"show me roses"` - Just flower type
- `"clear everything"` - Reset memory
- `"remove colors"` - Remove filter

---

## Expected Behavior

### ✅ Should Work
- All basic filters (color, budget, DIY, occasion)
- Complex combinations
- Memory persistence across messages
- Filter removal

### ⚠️ May Differ from v6
- **Count differences:** MySQL has fewer rows (no color expansion)
- **Product names:** MySQL doesn't include color suffixes
- **NULL handling:** Some differences due to data structure

---

## Debugging

### If queries fail:

1. **Check SQL syntax:**
   - Look for MySQL-specific errors
   - Verify window functions are supported

2. **Check result format:**
   - Ensure rows are dictionaries
   - Check `run_sql()` conversion logic

3. **Check database connection:**
   - Verify MySQL credentials
   - Test simple query: `SELECT * FROM flowers_view LIMIT 1`

### Enable Debug Mode:
```python
bot = FlowerConsultant(debug=True)
bot.ask("red flowers")
```

This will show:
- Memory state
- Generated SQL
- Execution time
- Results

---

## Success Criteria

✅ **All tests pass:**
- Queries execute without SQL errors
- Results are returned and formatted correctly
- Memory persists across messages
- Filters can be added/removed

✅ **Ready for production when:**
- All test queries work
- No SQL errors
- Results match expected format
- Performance is acceptable

---

## Next Steps After Testing

1. **If all tests pass:**
   - Deploy v7 to production
   - Update any deployment scripts
   - Monitor for any issues

2. **If tests fail:**
   - Check error messages
   - Review SQL queries
   - Verify database connection
   - Check VIEW is applied correctly

---

## Files Created

- `v7_chat_bot.py` - MySQL version of chatbot
- `web_demo_v2.py` - Web demo using v7
- `test_v7_iterative.py` - Test script
- `create_flowers_view_final.sql` - Final VIEW with all fixes

All ready for testing!

