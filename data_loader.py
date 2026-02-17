"""Data loader: fetches unit data from a published Google Sheet (CSV)."""
import csv
import io
import requests
from config import SHEET_URL

# ── Yes/No boolean fields ─────────────────────────────────────────────
BOOLEAN_FIELDS = {
    "utilities_included",
    "electric_included",
    "parking_optional",
    "parking_available",
    "wifi_optional",
    "wifi_cancel_anytime",
    "cats_allowed",
    "dogs_allowed",
    "breed_restrictions_apply",
}

# ── Numeric (money / percentage) fields ────────────────────────────────
NUMERIC_FIELDS = {
    "base_rent",
    "wsg_monthly",
    "security_deposit",
    "application_fee",
    "cleaning_fee",
    "holding_fee_percent",
    "parking_monthly_cost",
    "wifi_monthly_cost",
    "wifi_device_limit",
    "pet_rent_monthly",
}

# ── In‑memory cache ───────────────────────────────────────────────────
_cache: list[dict] | None = None


def _normalize_header(header: str) -> str:
    """Lowercase, strip, replace spaces with underscores."""
    return header.strip().lower().replace(" ", "_")


def _to_bool(value: str) -> bool:
    """Convert Yes/No string to bool (case‑insensitive)."""
    return value.strip().lower() in ("yes", "y", "true", "1")


def _to_number(value: str) -> float:
    """Strip currency symbols and commas, return float."""
    cleaned = value.strip().replace("$", "").replace(",", "")
    if not cleaned:
        return 0.0
    return float(cleaned)


def _parse_row(row: dict[str, str]) -> dict:
    """Normalize a single CSV row into a typed unit dict."""
    unit: dict = {}
    for raw_key, raw_val in row.items():
        key = _normalize_header(raw_key)
        val = raw_val.strip() if raw_val else ""

        if key in BOOLEAN_FIELDS:
            unit[key] = _to_bool(val)
        elif key in NUMERIC_FIELDS:
            unit[key] = _to_number(val)
        else:
            unit[key] = val

    return unit


# ── Public API ─────────────────────────────────────────────────────────

def refresh_data() -> list[dict]:
    """Re‑fetch data from Google Sheets and update cache."""
    global _cache

    if not SHEET_URL:
        raise ValueError(
            "SHEET_URL is not configured. "
            "Set it in config.py or via the SHEET_URL environment variable."
        )

    resp = requests.get(SHEET_URL, timeout=15)
    resp.raise_for_status()

    content = resp.text
    # Handle UTF-8 BOM
    if content.startswith("\ufeff"):
        content = content[1:]

    reader = csv.DictReader(io.StringIO(content))
    _cache = [_parse_row(row) for row in reader]
    return _cache


def get_all_units() -> list[dict]:
    """Return all units (fetches on first call)."""
    global _cache
    if _cache is None:
        refresh_data()
    return _cache  # type: ignore[return-value]


def get_unit(unit_id: str) -> dict | None:
    """Return a single unit by unit_id, or None."""
    for unit in get_all_units():
        if str(unit.get("unit_id", "")).strip() == str(unit_id).strip():
            return unit
    return None
