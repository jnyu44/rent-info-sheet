"""Flask web application for the Rent Info PDF tool."""
from flask import Flask, render_template, request, jsonify, Response
from data_loader import get_all_units, get_unit, refresh_data
from compute import compute_unit_totals
from pdf_renderer import render_html, render_pdf
from config import HOST, PORT, DEBUG

app = Flask(__name__)


@app.route("/")
def index():
    """Main page with unit selector and override form."""
    return render_template("index.html")


@app.route("/api/units")
def api_units():
    """List all units (id + address + unit number)."""
    try:
        units = get_all_units()
        summary = [
            {
                "unit_id": u.get("unit_id", ""),
                "street_address": u.get("street_address", ""),
                "unit_number": u.get("unit_number", ""),
            }
            for u in units
        ]
        return jsonify({"success": True, "units": summary})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/units/<unit_id>")
def api_unit(unit_id):
    """Return full data for a single unit."""
    try:
        unit = get_unit(unit_id)
        if not unit:
            return jsonify({"success": False, "error": "Unit not found"}), 404
        return jsonify({"success": True, "unit": unit})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    """Re‑fetch data from Google Sheets."""
    try:
        units = refresh_data()
        return jsonify({"success": True, "count": len(units)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/preview/<unit_id>", methods=["GET", "POST"])
def preview(unit_id):
    """Render an HTML preview of the rental info sheet."""
    try:
        unit = get_unit(unit_id)
        if not unit:
            return "Unit not found", 404

        overrides = request.get_json(silent=True) or {}
        # Convert override numeric strings to floats
        numeric_keys = [
            "base_rent", "security_deposit", "application_fee",
            "cleaning_fee", "holding_fee_percent", "parking_monthly_cost",
            "wifi_monthly_cost", "wifi_device_limit", "pet_rent_monthly",
            "wsg_monthly",
        ]
        for k in numeric_keys:
            if k in overrides and overrides[k] not in (None, ""):
                try:
                    overrides[k] = float(str(overrides[k]).replace("$", "").replace(",", ""))
                except ValueError:
                    pass

        ctx = compute_unit_totals(unit, overrides if overrides else None)
        html = render_html(ctx)
        return html
    except Exception as e:
        return f"Error: {e}", 500


@app.route("/download/<unit_id>", methods=["POST"])
def download(unit_id):
    """Generate and download the PDF."""
    try:
        unit = get_unit(unit_id)
        if not unit:
            return jsonify({"success": False, "error": "Unit not found"}), 404

        overrides = request.get_json(silent=True) or {}
        numeric_keys = [
            "base_rent", "security_deposit", "application_fee",
            "cleaning_fee", "holding_fee_percent", "parking_monthly_cost",
            "wifi_monthly_cost", "wifi_device_limit", "pet_rent_monthly",
            "wsg_monthly",
        ]
        for k in numeric_keys:
            if k in overrides and overrides[k] not in (None, ""):
                try:
                    overrides[k] = float(str(overrides[k]).replace("$", "").replace(",", ""))
                except ValueError:
                    pass

        ctx = compute_unit_totals(unit, overrides if overrides else None)
        pdf_bytes = render_pdf(ctx)

        address = ctx.get("street_address", "unit")
        unit_num = ctx.get("unit_number", "")
        filename = f"Rental_Info_{address}_{unit_num}.pdf".replace(" ", "_")

        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", PORT))
    app.run(debug=DEBUG, host=HOST, port=port)
