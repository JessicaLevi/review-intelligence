
import os

from dotenv import load_dotenv
from supabase import Client, create_client

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def get_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise ValueError(
            "SUPABASE_URL dan SUPABASE_SERVICE_ROLE_KEY "
            "harus tersedia di file .env"
        )

    return create_client(url, key)
