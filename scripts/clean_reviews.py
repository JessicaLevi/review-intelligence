
import html
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_ROOT / "data" / "reviews_raw.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "reviews_clean.csv"


def clean_text(value):
    """Clean review text while preserving emojis and sentiment signals."""
    if pd.isna(value) or value is None:
        return ""

    text = html.unescape(str(value))
    text = unicodedata.normalize("NFC", text)

    # Remove HTML tags, if any
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove URLs from review text
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)

    # Remove control characters but preserve newlines and tabs for normalization
    text = "".join(
        char for char in text
        if char in "\n\t" or unicodedata.category(char) != "Cc"
    )

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Intentionally preserve emojis, punctuation, and repeated expressive marks
    return text


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Raw data not found: {INPUT_FILE}. "
            "Run scripts/fetch_reviews.py first."
        )

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        records = json.load(file)

    df = pd.DataFrame(records)
    initial_count = len(df)

    required_columns = [
        "reviewId",
        "title",
        "text",
        "textTranslated",
        "stars",
        "publishedAtDate",
        "reviewUrl",
    ]

    for column in required_columns:
        if column not in df.columns:
            df[column] = None

    # Use the translated text when available; otherwise use the original
    translated = df["textTranslated"].map(clean_text)
    original = df["text"].map(clean_text)

    df["review_text"] = translated.where(
        translated.ne(""),
        original,
    )

    # Standardize fields for downstream processing
    df["review_id"] = df["reviewId"].astype("string").str.strip()
    df["restaurant_name"] = df["title"].map(clean_text)
    df["stars"] = pd.to_numeric(df["stars"], errors="coerce")

    df["published_at"] = pd.to_datetime(
        df["publishedAtDate"],
        errors="coerce",
        utc=True,
    )

    df["review_url"] = df["reviewUrl"].map(clean_text)

    # Drop records without usable review text or a stable unique ID
    df = df[df["review_text"].ne("")]
    df = df[df["review_id"].notna() & df["review_id"].ne("")]

    # Keep one record per review ID
    df = df.drop_duplicates(subset=["review_id"], keep="first")

    # Ratings should be between 1 and 5; invalid ratings become missing
    df.loc[~df["stars"].between(1, 5), "stars"] = pd.NA

    output_columns = [
        "review_id",
        "restaurant_name",
        "review_text",
        "stars",
        "published_at",
        "review_url",
    ]

    cleaned = df[output_columns].copy()
    cleaned["published_at"] = cleaned["published_at"].map(
        lambda value: value.isoformat() if pd.notna(value) else None
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print("=== Cleaning Summary ===")
    print(f"Raw records: {initial_count}")
    print(f"Clean records: {len(cleaned)}")
    print(f"Removed records: {initial_count - len(cleaned)}")
    print(f"Duplicate review IDs remaining: {cleaned['review_id'].duplicated().sum()}")
    print(f"Missing review text: {cleaned['review_text'].eq('').sum()}")
    print(f"Missing ratings: {cleaned['stars'].isna().sum()}")
    print(f"Output: {OUTPUT_FILE}")

    print("\nSample cleaned reviews:")
    print(cleaned.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
