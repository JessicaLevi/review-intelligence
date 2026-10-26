
cat > scripts/analyze_sentiment.py <<'PY'
import html
import os
import re
import unicodedata
from datetime import datetime, timezone

import emoji
from supabase import create_client
from transformers import pipeline


MODEL_NAME = "w11wo/indonesian-roberta-base-sentiment-classifier"
INFERENCE_BATCH_SIZE = 8
UPLOAD_BATCH_SIZE = 100


def get_supabase_client():
    url = os.getenv("SUPABASE_URL") or os.getenv(
        "NEXT_PUBLIC_SUPABASE_URL"
    )
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise ValueError(
            "SUPABASE_URL dan SUPABASE_SERVICE_ROLE_KEY "
            "harus tersedia sebagai environment variables."
        )

    return create_client(url, key)


def clean_review_text(value):
    """Cleaning konservatif mengikuti notebook."""
    if value is None:
        return ""

    text = html.unescape(str(value))
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = emoji.demojize(text, language="en")
    text = re.sub(r"\s+", " ", text).strip()

    return text


def normalize_label(label):
    """Mapping label mengikuti notebook hands-on."""
    label = str(label).lower().strip()

    if "pos" in label or label in {"label_2", "2"}:
        return "positive"

    if "neg" in label or label in {"label_0", "0"}:
        return "negative"

    if "neu" in label or label in {"label_1", "1"}:
        return "neutral"

    raise ValueError(
        f"Label model tidak dikenali: {label!r}. "
        "Periksa classifier.model.config.id2label."
    )


def fetch_all_rows(client, table, columns):
    """Mengambil seluruh data dengan pagination."""
    rows = []
    start = 0
    page_size = 500

    while True:
        response = (
            client.table(table)
            .select(columns)
            .range(start, start + page_size - 1)
            .execute()
        )

        page = response.data or []
        rows.extend(page)

        if len(page) < page_size:
            break

        start += page_size

    return rows


def main():
    client = get_supabase_client()

    reviews = fetch_all_rows(
        client,
        "reviews",
        "review_id,review_text",
    )

    existing = fetch_all_rows(
        client,
        "review_sentiment",
        "review_id",
    )

    analyzed_ids = {
        row["review_id"]
        for row in existing
        if row.get("review_id")
    }

    pending = []

    for review in reviews:
        review_id = review.get("review_id")
        raw_text = review.get("review_text")

        if not review_id or not raw_text:
            continue

        if review_id in analyzed_ids:
            continue

        cleaned_text = clean_review_text(raw_text)

        if cleaned_text:
            pending.append({
                "review_id": review_id,
                "text": cleaned_text,
            })

    print(f"Reviews in Supabase: {len(reviews)}")
    print(f"Already analyzed: {len(analyzed_ids)}")
    print(f"Pending analysis: {len(pending)}")

    if not pending:
        print("No new reviews to analyze.")
        return

    classifier = pipeline(
        task="text-classification",
        model=MODEL_NAME,
        tokenizer=MODEL_NAME,
        device=-1,
    )

    # Periksa konfigurasi model sebelum memproses seluruh data.
    id2label = classifier.model.config.id2label
    print("Model:", MODEL_NAME)
    print("Model id2label:", id2label)

    # Notebook menggunakan LABEL_2=positive,
    # LABEL_1=neutral, LABEL_0=negative.
    # Jika konfigurasi model berbeda, hentikan proses agar
    # tidak menyimpan hasil dengan sentimen yang terbalik.
    expected = {
        "LABEL_0": "negative",
        "LABEL_1": "neutral",
        "LABEL_2": "positive",
    }

    normalized_config = {
        str(key).upper(): str(value).lower()
        for key, value in id2label.items()
    }

    for raw_label, expected_sentiment in expected.items():
        if raw_label in normalized_config:
            actual = normalized_config[raw_label]

            if expected_sentiment not in actual:
                raise ValueError(
                    "Konfigurasi label model tidak cocok dengan "
                    f"notebook: {raw_label}={actual!r}, "
                    f"seharusnya {expected_sentiment!r}. "
                    "Periksa id2label dan perbaiki normalize_label()."
                )

    results = []

    for start in range(0, len(pending), INFERENCE_BATCH_SIZE):
        batch = pending[start:start + INFERENCE_BATCH_SIZE]
        texts = [item["text"] for item in batch]

        predictions = classifier(
            texts,
            batch_size=INFERENCE_BATCH_SIZE,
            truncation=True,
            max_length=256,
        )

        for item, prediction in zip(batch, predictions):
            results.append({
                "review_id": item["review_id"],
                "sentiment_label": normalize_label(
                    prediction["label"]
                ),
                "sentiment_score": float(prediction["score"]),
                "model_name": MODEL_NAME,
                "analyzed_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            })

        print(
            f"Analyzed {min(start + len(batch), len(pending))}"
            f"/{len(pending)}"
        )

    for start in range(0, len(results), UPLOAD_BATCH_SIZE):
        batch = results[start:start + UPLOAD_BATCH_SIZE]

        (
            client.table("review_sentiment")
            .upsert(batch, on_conflict="review_id")
            .execute()
        )

        print(
            f"Saved {min(start + len(batch), len(results))}"
            f"/{len(results)} results"
        )

    print("Sentiment analysis completed successfully.")


if __name__ == "__main__":
    main()
PY
