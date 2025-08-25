import pandas as pd
from sqlalchemy import create_engine
import os

# -------- CONFIG --------
FILE_PATH = "data/BloombrainCatalogwithprices.xlsx"
TABLE_NAME = "flower_catalog"
# Example: postgres://username:password@host:port/dbname
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/flowers")
# ------------------------

def main():
    # Load Excel
    df = pd.read_excel(FILE_PATH)

    # ✅ Clean semicolon-separated fields into lists (JSONB friendly)
    multi_cols = ["Colors", "Seasonality", "Weekdays", "Tags"]
    for col in multi_cols:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: [v.strip() for v in str(x).split(";")] if pd.notnull(x) else []
            )

    # ✅ Connect to Postgres
    engine = create_engine(DATABASE_URL)

    # ✅ Push to Postgres
    df.to_sql(TABLE_NAME, engine, if_exists="replace", index=False)

    print(f"Uploaded {len(df)} rows to {TABLE_NAME} in {DATABASE_URL}")

if __name__ == "__main__":
    main()
