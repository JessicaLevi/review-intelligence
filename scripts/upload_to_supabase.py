
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.review_pipeline.supabase_client import get_supabase_client

INPUT_FILE = ROOT / "data" / "reviews_clean.csv"
TABLE_NAME = "reviews"
BATCH_SIZE = 100


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            "reviews_clean.csv tidak ditemukan. "
            "Jalankan python scripts/clean_reviews.py terlebih dahulu."
        )

    df = pd.read_csv(INPUT_FILE)

    # Convert missing CSV values into JSON-compatible None
    df = df.astype(object).where(pd.notna(df), None)

    records = df.to_dict(orient="records")

    if not records:
        print("Tidak ada review untuk di-upload.")
        return

    supabase = get_supabase_client()

    for start in range(0, len(records), BATCH_SIZE):
        batch = records[start:start + BATCH_SIZE]

        response = (
            supabase.table(TABLE_NAME)
            .upsert(batch, on_conflict="review_id")
            .execute()
        )

        print(
            f"Batch {start // BATCH_SIZE + 1}: "
            f"{len(batch)} records diproses."
        )

    print(f"Selesai. {len(records)} review diproses ke Supabase.")


if __name__ == "__main__":
    main()
