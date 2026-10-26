
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load .env dari root project
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

API_TOKEN = os.getenv("APIFY_API_TOKEN")
DATASET_ID = os.getenv("APIFY_DATASET_ID")

if not API_TOKEN or not DATASET_ID:
    raise ValueError(
        "APIFY_API_TOKEN dan APIFY_DATASET_ID "
        "harus diisi di file .env"
    )

url = (
    f"https://api.apify.com/v2/datasets/"
    f"{DATASET_ID}/items"
)

params = {
    "token": API_TOKEN,
    "format": "json",
    "limit": 1000,
}

response = requests.get(url, params=params, timeout=60)
response.raise_for_status()

reviews = response.json()

if not isinstance(reviews, list):
    raise ValueError("Respons Apify bukan berupa list data.")

output_dir = PROJECT_ROOT / "data"
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "reviews_raw.json"

with output_file.open("w", encoding="utf-8") as file:
    json.dump(reviews, file, ensure_ascii=False, indent=2)

print(f"Jumlah review yang diambil: {len(reviews)}")
print(f"File tersimpan: {output_file}")

if reviews:
    print("\nKolom yang tersedia:")
    print(list(reviews[0].keys()))

    print("\nContoh satu review:")
    print(json.dumps(reviews[0], ensure_ascii=False, indent=2))
else:
    print("Dataset kosong. Periksa kembali Dataset ID.")
