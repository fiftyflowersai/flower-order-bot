CREATE OR REPLACE VIEW flowers_view AS
SELECT
  CONCAT(p.product_id, '_', COALESCE(pv.product_variant_id, '0')) AS unique_id,
  p.name AS product_name,
  pv.name AS variant_name,
  pv.price AS variant_price,
  
  -- Description (not JSON, keep as is)
  (SELECT pav.value FROM product_attribute_values pav
   WHERE pav.product_id = p.product_id AND pav.attribute_id = 1 LIMIT 1) AS description_clean,
  
  -- Colors aggregated
  (SELECT GROUP_CONCAT(c.name ORDER BY c.name SEPARATOR '; ')
   FROM product_colors_link pcl
   JOIN colors c ON pcl.color_id = c.color_id
   WHERE pcl.product_id = p.product_id AND c.status = 'active') AS colors_raw,
  
  -- Color booleans
  EXISTS(SELECT 1 FROM product_colors_link pcl JOIN colors c ON pcl.color_id = c.color_id
         WHERE pcl.product_id = p.product_id AND c.status = 'active'
         AND LOWER(c.name) IN ('red', 'true red', 'wine red', 'cranberry', 'burgundy', 'rust')) AS has_red,
  EXISTS(SELECT 1 FROM product_colors_link pcl JOIN colors c ON pcl.color_id = c.color_id
         WHERE pcl.product_id = p.product_id AND c.status = 'active'
         AND LOWER(c.name) IN ('pink', 'true pink', 'hot pink', 'dusty pink', 'light pink',
                               'blush', 'dusty rose', 'mauve', 'pinky lavender', 'fuchsia',
                               'magenta', 'coral')) AS has_pink,
  EXISTS(SELECT 1 FROM product_colors_link pcl JOIN colors c ON pcl.color_id = c.color_id
         WHERE pcl.product_id = p.product_id AND c.status = 'active'
         AND LOWER(c.name) IN ('white', 'ivory', 'natural', 'champagne', 'clear')) AS has_white,
  EXISTS(SELECT 1 FROM product_colors_link pcl JOIN colors c ON pcl.color_id = c.color_id
         WHERE pcl.product_id = p.product_id AND c.status = 'active'
         AND LOWER(c.name) IN ('yellow', 'pale yellow', 'mustard yellow', 'dark yellow',
                               'amber', 'chartreuse', 'gold')) AS has_yellow,
  EXISTS(SELECT 1 FROM product_colors_link pcl JOIN colors c ON pcl.color_id = c.color_id
         WHERE pcl.product_id = p.product_id AND c.status = 'active'
         AND LOWER(c.name) IN ('orange', 'peach', 'sunset', 'terracotta', 'copper',
                               'dark orange', 'true orange')) AS has_orange,
  EXISTS(SELECT 1 FROM product_colors_link pcl JOIN colors c ON pcl.color_id = c.color_id
         WHERE pcl.product_id = p.product_id AND c.status = 'active'
         AND LOWER(c.name) IN ('purple', 'lavender', 'pinky lavender', 'true purple', 'dark purple')) AS has_purple,
  EXISTS(SELECT 1 FROM product_colors_link pcl JOIN colors c ON pcl.color_id = c.color_id
         WHERE pcl.product_id = p.product_id AND c.status = 'active'
         AND LOWER(c.name) IN ('blue', 'soft blue', 'light blue', 'teal')) AS has_blue,
  EXISTS(SELECT 1 FROM product_colors_link pcl JOIN colors c ON pcl.color_id = c.color_id
         WHERE pcl.product_id = p.product_id AND c.status = 'active'
         AND LOWER(c.name) IN ('green', 'sage green', 'emerald green', 'forest green',
                               'lime green', 'light green', 'true green')) AS has_green,
  
  -- Seasonality Range 1 (FIXED: Explicit NULL handling when available_dates IS NULL)
  CASE 
    WHEN pa.available_dates IS NULL THEN NULL
    ELSE JSON_EXTRACT(pa.available_dates, '$[0].start_month')
  END AS season_start_month,
  CASE 
    WHEN pa.available_dates IS NULL THEN NULL
    ELSE JSON_EXTRACT(pa.available_dates, '$[0].start_day')
  END AS season_start_day,
  CASE 
    WHEN pa.available_dates IS NULL THEN NULL
    ELSE JSON_EXTRACT(pa.available_dates, '$[0].end_month')
  END AS season_end_month,
  CASE 
    WHEN pa.available_dates IS NULL THEN NULL
    ELSE JSON_EXTRACT(pa.available_dates, '$[0].end_day')
  END AS season_end_day,
  
  -- Seasonality Range 2 (for products with multiple availability ranges)
  CASE 
    WHEN pa.available_dates IS NULL THEN NULL
    ELSE JSON_EXTRACT(pa.available_dates, '$[1].start_month')
  END AS season_range_2_start_month,
  CASE 
    WHEN pa.available_dates IS NULL THEN NULL
    ELSE JSON_EXTRACT(pa.available_dates, '$[1].start_day')
  END AS season_range_2_start_day,
  CASE 
    WHEN pa.available_dates IS NULL THEN NULL
    ELSE JSON_EXTRACT(pa.available_dates, '$[1].end_month')
  END AS season_range_2_end_month,
  CASE 
    WHEN pa.available_dates IS NULL THEN NULL
    ELSE JSON_EXTRACT(pa.available_dates, '$[1].end_day')
  END AS season_range_2_end_day,
  
  -- Seasonality Range 3 (for products with three availability ranges)
  CASE 
    WHEN pa.available_dates IS NULL THEN NULL
    ELSE JSON_EXTRACT(pa.available_dates, '$[2].start_month')
  END AS season_range_3_start_month,
  CASE 
    WHEN pa.available_dates IS NULL THEN NULL
    ELSE JSON_EXTRACT(pa.available_dates, '$[2].start_day')
  END AS season_range_3_start_day,
  CASE 
    WHEN pa.available_dates IS NULL THEN NULL
    ELSE JSON_EXTRACT(pa.available_dates, '$[2].end_month')
  END AS season_range_3_end_month,
  CASE 
    WHEN pa.available_dates IS NULL THEN NULL
    ELSE JSON_EXTRACT(pa.available_dates, '$[2].end_day')
  END AS season_range_3_end_day,
  
  -- is_year_round (FIXED: Don't default NULL to TRUE)
  CASE
    WHEN JSON_EXTRACT(pa.available_dates, '$[0].start_month') = 1
     AND JSON_EXTRACT(pa.available_dates, '$[0].start_day') = 1
     AND JSON_EXTRACT(pa.available_dates, '$[0].end_month') = 12
     AND JSON_EXTRACT(pa.available_dates, '$[0].end_day') = 31
    THEN TRUE
    WHEN pa.available_dates IS NULL THEN NULL
    ELSE FALSE
  END AS is_year_round,
  
  -- seasonality (FIXED: Extract first element from JSON array, join multiple with semicolon)
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
  
  -- diy_level (FIXED: Extract first element from JSON array, handle empty arrays)
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
  
  -- holiday_occasion (FIXED: Extract first element from JSON array, or join multiple with semicolon)
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
  
  -- product_type_all_flowers (FIXED: Extract first element from JSON array, handle empty arrays)
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
  
  -- recipe_metafield (check if this is JSON too)
  (SELECT pav.value FROM product_attribute_values pav
   WHERE pav.product_id = p.product_id AND pav.attribute_id = 415 LIMIT 1) AS recipe_metafield,
  
  -- non_color_options (aggregated from variant_options, exclude color-related options)
  -- Note: This field is only used for display, not in WHERE clauses
  (SELECT GROUP_CONCAT(
      DISTINCT CONCAT(vo.label, ': ', vov.value) 
      SEPARATOR '; '
    )
   FROM product_variants pv2
   JOIN variant_options vo ON pv2.product_variant_id = vo.product_variant_id
   LEFT JOIN variant_option_values vov ON vo.variant_option_id = vov.variant_option_id
   WHERE pv2.product_id = p.product_id
     AND vo.status = 'active'
     AND (vov.status = 'active' OR vov.status IS NULL)
     AND vo.label NOT LIKE '%color%'
     AND vo.label NOT LIKE '%Color%'
     AND vo.label NOT LIKE '%Colour%'
   LIMIT 1) AS non_color_options,
  
  -- group_category (FIXED: Extract first element from JSON array, handle empty arrays)
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

FROM products p
LEFT JOIN product_variants pv ON p.product_id = pv.product_id AND pv.status = 'active'
LEFT JOIN product_availability pa ON p.product_id = pa.product_id
WHERE p.status = 'active';

