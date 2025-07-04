from flask import Flask, request, jsonify, abort
import pandas as pd
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
from dotenv import load_dotenv
load_dotenv()

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

    per_page = 1000
    start = (page - 1) * per_page
    end = start + per_page
    paginated_data = data[start:end]

    # Determine if there’s a next page
    has_more = end < len(data)
    next_page_url = None

    if has_more:
        # Dynamically build full URL for next page
        base_url = request.base_url  # e.g., http://localhost:5000/items
        query_params = request.args.to_dict()
        query_params['page'] = page + 1
        next_page_url = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in query_params.items())}"

    return jsonify({
        "page": page,
        "per_page": per_page,
        "total": len(data),
        "has_more": has_more,
        "next_page_url": next_page_url,
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

