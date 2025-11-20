CREATE VIEW flowers_view AS
SELECT
  CONCAT(p.product_id, '_', COALESCE(pv.product_variant_id, '0')) AS unique_id,
  p.name AS product_name,
  pv.name AS variant_name,
  pv.price AS variant_price,
  -- Description
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
  -- Seasonality
  COALESCE(JSON_EXTRACT(pa.available_dates, '$[0].start_month'), 1) AS season_start_month,
  COALESCE(JSON_EXTRACT(pa.available_dates, '$[0].start_day'), 1) AS season_start_day,
  COALESCE(JSON_EXTRACT(pa.available_dates, '$[0].end_month'), 12) AS season_end_month,
  COALESCE(JSON_EXTRACT(pa.available_dates, '$[0].end_day'), 31) AS season_end_day,
  CASE
    WHEN JSON_EXTRACT(pa.available_dates, '$[0].start_month') = 1
     AND JSON_EXTRACT(pa.available_dates, '$[0].start_day') = 1
     AND JSON_EXTRACT(pa.available_dates, '$[0].end_month') = 12
     AND JSON_EXTRACT(pa.available_dates, '$[0].end_day') = 31
    THEN TRUE
    WHEN pa.available_dates IS NULL THEN TRUE
    ELSE FALSE
  END AS is_year_round,
  (SELECT pav.value FROM product_attribute_values pav
   WHERE pav.product_id = p.product_id AND pav.attribute_id = 56 LIMIT 1) AS seasonality,
  -- Filters
  (SELECT pav.value FROM product_attribute_values pav
   WHERE pav.product_id = p.product_id AND pav.attribute_id = 370 LIMIT 1) AS diy_level,
  (SELECT pav.value FROM product_attribute_values pav
   WHERE pav.product_id = p.product_id AND pav.attribute_id = 374 LIMIT 1) AS holiday_occasion,
  (SELECT pav.value FROM product_attribute_values pav
   WHERE pav.product_id = p.product_id AND pav.attribute_id = 371 LIMIT 1) AS product_type_all_flowers,
  (SELECT pav.value FROM product_attribute_values pav
   WHERE pav.product_id = p.product_id AND pav.attribute_id = 415 LIMIT 1) AS recipe_metafield,
  (SELECT pav.value FROM product_attribute_values pav
   WHERE pav.product_id = p.product_id AND pav.attribute_id = 365 LIMIT 1) AS group_category
FROM products p
LEFT JOIN product_variants pv ON p.product_id = pv.product_id AND pv.status = 'active'
LEFT JOIN product_availability pa ON p.product_id = pa.product_id
WHERE p.status = 'active';