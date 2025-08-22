# FiftyFlowers Chatbot – EDA & Preprocessing Report

## 1) Objective

Prepare the product catalog for a website chatbot that helps customers discover, filter, and select products (e.g., by color, type, price, and delivery day). This report documents the dataset, preprocessing decisions, and canonical dictionaries the chatbot will use for reliable filtering and natural-language queries.

## 2) Data Summary

- Source file: `data/BloombrainCatalogwithprices.xlsx`

- Shape: **27,680 rows × 122 columns**


<details>
<summary>pandas DataFrame info</summary>


```
<class 'pandas.core.frame.DataFrame'>
RangeIndex: 27680 entries, 0 to 27679
Columns: 122 entries, Hash version to attributes.Intimate Package Includes
dtypes: float64(9), int64(1), object(112)
memory usage: 25.8+ MB
```

</details>


**Top Missing Columns (20)**


```
                                    Missing Count  Missing %
attributes.Average Garland Height           27679  99.996387
attributes.Open Text 3                      27677  99.989162
attributes.Arch Size                        27677  99.989162
attributes.Average Spike Size               27675  99.981936
attributes.Boutonniere Recipe               27674  99.978324
attributes.Wedding Bouquet Recipe           27674  99.978324
attributes.Open Text 2                      27672  99.971098
attributes.Average Globe Size               27671  99.967486
attributes.Foams Purpose                    27670  99.963873
attributes.Average Diameter                 27664  99.942197
attributes.Average Width                    27655  99.909682
attributes.PDF Recipe                       27655  99.909682
attributes.Garland & Wreath Height          27650  99.891618
attributes.Average Pod Width                27645  99.873555
attributes.Average Branch Length            27642  99.862717
attributes.Branches Per Bunch               27642  99.862717
attributes.Average Total Length             27633  99.830202
attributes.Average Leaf Width               27623  99.794075
attributes.Average Bloom Size               27620  99.783237
attributes.Average Corsage Height           27616  99.768786
```


**Top Unique Count Columns (20)**


```
Variant ID                             18653
Option value ID                         9933
Product name                            4935
Product ID                              4935
attributes.Description                  4705
attributes.SEO Title                    4662
attributes.Shopify Tags                 4599
attributes.SEO Description              2889
Variant name                            1770
Option ID                               1603
Colors (by semicolon)                    942
attributes.Recipe metafield              883
Option value label                       855
Tags (by semicolon)                      829
attributes.Recipe description            660
attributes.Size Breakdown                555
attributes.Color Description             536
Hash version                             446
attributes.Holiday Occasion              414
Option value (variant ID reference)      405
dtype: int64
```

## 3) Preprocessing Decisions

- Drop columns with ≥99% missing values to reduce noise.

- Normalize semicolon-delimited fields into lists: **Colors**, **Tags**, **Weekdays**.

- Standardize strings (lowercase, trim) and normalize weekdays to `mon..sun`.

- Introduce **canonical dictionaries** for colors and weekdays to enable consistent filtering and synonym handling.

- Keep high-signal fields for chatbot retrieval (e.g., Product name, Group, Subgroup, Colors, Tags, Weekdays, prices, statuses).

## 4) Files Emitted

- `raw_values.json` – raw unique tokens extracted from dataset for: colors, tags, weekdays, group, subgroup.

- `colors.json` – canonical **color buckets expanded from real data** (+ `_unassigned` for review).

- `weekdays.json` – canonical weekday map (mon..sun → synonyms seen in data) + `misc` if any.

- `canonical_dict.json` – combined canonical file (back-compat).

## 5) Key Value Snapshots

**Top Colors (token frequency, semicolon-split)**

- white: 5766
- pink: 3619
- farm mixes: 3552
- yellow: 3533
- hot pink: 3340
- red: 3339
- green: 3229
- orange: 3186
- lavender: 3070
- light pink: 2807
- ivory: 2488
- peach: 2483
- chartreuse: 1733
- sage green: 1458
- purple: 1373
- blush: 1258
- pale yellow: 838
- rainbow: 796
- forest green: 774
- wine red: 768


**Top Tags (token frequency, semicolon-split)**

- jardines: 1012
- multiple: 857
- b tinted: 627
- natuflora +vase: 414
- florist combo: 348
- bouquet natuflora: 309
- florida garland: 297
- agrogana +vase: 279
- new: 275
- sa: 243
- wedding: 240
- flyboy freeze b: 234
- blossom | natuflora: 227
- standard: 215
- potomac bda: 209
- mini calla - sa: 202
- natuflora: 189
- shuster dried: 180
- florist: 180
- elite: 171


**Weekdays Availability (token frequency, semicolon-split)**

- fri: 27679
- tue: 27675
- wed: 27675
- thu: 27675
- sat: 27176
- mon: 25551


## 6) Next Steps

- Review `colors.json` `_unassigned` bucket and either map or leave excluded from filters.

- Generate a **clean catalog export** (normalized columns, list fields JSON-encoded) for loading into SQL.

- Choose hosting for SQL (e.g., **Supabase Postgres** or **PlanetScale MySQL** for cost-effective scaling).

- Implement chatbot retrieval flow: parse intent → map synonyms via canonical JSONs → build SQL where-clause → return ranked products.
