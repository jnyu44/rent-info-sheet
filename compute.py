"""Deterministic computation engine for rental information.

All monetary calculations use Decimal to avoid floating‑point drift.
Every function is pure — no side effects, no I/O.
"""
from decimal import Decimal, ROUND_HALF_UP

TWO_PLACES = Decimal("0.01")


def _d(value) -> Decimal:
    """Coerce any value to Decimal."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _money(value: Decimal) -> str:
    """Format a Decimal as a dollar string: $1,234.56 or $1,234 if whole."""
    rounded = value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    if rounded == rounded.to_integral_value():
        return f"${int(rounded):,}"
    return f"${rounded:,.2f}"


def compute_unit_totals(unit: dict, overrides: dict | None = None) -> dict:
    """Merge overrides into unit data and compute all derived fields.

    Parameters
    ----------
    unit : dict
        Raw unit data from the data loader.
    overrides : dict | None
        Session‑only overrides (same keys as unit). Not persisted.

    Returns
    -------
    dict
        Complete context ready for template rendering.
    """
    # Merge: overrides win
    data = {**unit}
    if overrides:
        for k, v in overrides.items():
            if v not in (None, ""):
                data[k] = v

    # ── Pull values ────────────────────────────────────────────────────
    base_rent       = _d(data.get("base_rent", 0))
    security_dep    = _d(data.get("security_deposit", 0))
    app_fee         = _d(data.get("application_fee", 0))
    cleaning_fee    = _d(data.get("cleaning_fee", 0))
    holding_pct     = _d(data.get("holding_fee_percent", 25))

    # ── Derived amounts ────────────────────────────────────────────────
    first_month     = base_rent          # rule: equals base rent
    last_month      = base_rent          # rule: equals base rent
    holding_fee     = (base_rent * holding_pct / Decimal("100")).quantize(
        TWO_PLACES, rounding=ROUND_HALF_UP
    )
    total_move_in   = first_month + last_month + security_dep + app_fee + cleaning_fee
    remaining       = total_move_in - holding_fee

    # Utilities label
    utils_included = data.get("utilities_included", False)
    if isinstance(utils_included, str):
        utils_included = utils_included.strip().lower() in ("yes", "true", "1")
    utilities_label = "Included in Rent" if utils_included else data.get("utilities_text", "Not Included")

    # Total monthly housing
    total_monthly = base_rent  # If utilities included, just base rent

    # ── Build context ──────────────────────────────────────────────────
    ctx = {**data}
    ctx.update({
        # Formatted amounts
        "base_rent_fmt":         _money(base_rent),
        "first_month_rent_fmt":  _money(first_month),
        "last_month_rent_fmt":   _money(last_month),
        "security_deposit_fmt":  _money(security_dep),
        "application_fee_fmt":   _money(app_fee),
        "cleaning_fee_fmt":      _money(cleaning_fee),
        "holding_fee_fmt":       _money(holding_fee),
        "total_move_in_fmt":     _money(total_move_in),
        "remaining_fmt":         _money(remaining),
        "total_monthly_fmt":     _money(total_monthly),
        "holding_pct_fmt":       f"{int(holding_pct)}%",

        # Raw Decimals (for any further computation)
        "first_month_rent":      float(first_month),
        "last_month_rent":       float(last_month),
        "holding_fee":           float(holding_fee),
        "total_move_in":         float(total_move_in),
        "remaining_after_hold":  float(remaining),
        "total_monthly":         float(total_monthly),

        # Labels
        "utilities_label":       utilities_label,

        # Parking
        "parking_monthly_cost_fmt": _money(_d(data.get("parking_monthly_cost", 0))),

        # WiFi
        "wifi_monthly_cost_fmt":    _money(_d(data.get("wifi_monthly_cost", 0))),
        "wifi_device_limit":        int(data.get("wifi_device_limit", 0)),

        # Pet
        "pet_rent_monthly_fmt":     _money(_d(data.get("pet_rent_monthly", 0))),
    })

    return ctx
