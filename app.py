# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re

app = Flask(__name__)
# Replace the origin with your GitHub Pages URL once you deploy the frontend
CORS(app, resources={r"/*": {"origins": "*"}})

ZIP_CA_REGEX = re.compile(r"^[A-Za-z]\d[A-Za-z][\s-]?\d[A-Za-z]\d$")
ZIP_US_REGEX = re.compile(r"^\d{5}(-\d{4})?$")

def lookup_zip(zip_str: str):
    z = zip_str.strip()
    # Decide country format (simple heuristic)
    if ZIP_CA_REGEX.match(z):
        country = "CA"
        q = z.replace(" ", "")
    elif ZIP_US_REGEX.match(z):
        country = "US"
        q = z[:5]
    else:
        return None, None, "Invalid ZIP/Postal format"

    url = f"https://api.zippopotam.us/{country}/{q}"
    try:
        r = requests.get(url, timeout=8)
        if r.status_code != 200:
            return None, None, "Location not found"
        data = r.json()
        place = data["places"][0]
        city = place["place name"]
        region = place["state"] if country == "US" else place["state"]  # works for CA too
        return city, region, None
    except Exception as e:
        return None, None, "Lookup failed"

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}

@app.route("/geo/lookup", methods=["POST"])
def geo_lookup():
    payload = request.get_json(silent=True) or {}
    zip_code = payload.get("zip", "")
    if not zip_code:
        return jsonify({"error": "zip is required"}), 400

    city, region, err = lookup_zip(zip_code)
    if err:
        return jsonify({"error": err}), 404

    return jsonify({"city": city, "region": region})
