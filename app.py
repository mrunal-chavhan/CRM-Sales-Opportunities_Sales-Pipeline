from flask import Flask, request, jsonify, abort
import pandas as pd
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

# Load Excel data once at startup
df = pd.read_csv("sales_pipeline.csv")
data = df.to_dict(orient="records")

app = Flask(__name__)

# Set your API Key (secure it via environment variable in production)

API_KEY = os.getenv("API_KEY", "default-fallback-token")

# Rate limiting: 100 requests per hour per IP
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per hour"]
)

# Auth check for /items endpoint only
@app.before_request
def check_auth():
    if request.endpoint == "get_items":
        token = request.headers.get("Authorization")
        if token != f"Bearer {API_KEY}":
            abort(401, description="Unauthorized")

@app.route("/items")
def get_items():
    try:
        page = int(request.args.get("page", 1))  # Default to page 1
        if page < 1:
            raise ValueError
    except ValueError:
        return jsonify({"error": "Invalid page number"}), 400

    per_page = 1000  # Fixed records per page

    start = (page - 1) * per_page
    end = start + per_page
    paginated_data = data[start:end]

    return jsonify({
        "page": page,
        "per_page": per_page,
        "total": len(data),
        "data": paginated_data
    })

# Error handler: Unauthorized
@app.errorhandler(401)
def unauthorized(e):
    return jsonify({"error": str(e)}), 401

# Error handler: Rate limit exceeded
@app.errorhandler(429)
def rate_limit_exceeded(e):
    return jsonify({"error": "Rate limit exceeded"}), 429

if __name__ == "__main__":
    app.run()

