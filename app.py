# from flask import Flask, request, jsonify, abort
# import pandas as pd
# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address
# import os
# from dotenv import load_dotenv
# load_dotenv()

# # Load Excel data once at startup
# df = pd.read_csv("sales_pipeline.csv")
# data = df.to_dict(orient="records")

# app = Flask(__name__)

# # Set your API Key (secure it via environment variable in production)

# API_KEY = os.getenv("API_KEY", "default-fallback-token")

# # Rate limiting: 100 requests per hour per IP
# limiter = Limiter(
#     get_remote_address,
#     app=app,
#     default_limits=["100 per hour"]
# )

# # Auth check for /items endpoint only
# @app.before_request
# def check_auth():
#     if request.endpoint == "get_items":
#         token = request.headers.get("Authorization")
#         if token != f"Bearer {API_KEY}":
#             abort(401, description="Unauthorized")

# @app.route("/items")
# def get_items():
#     try:
#         page = int(request.args.get("page", 1))  # Default to page 1
#         if page < 1:
#             raise ValueError
#     except ValueError:
#         return jsonify({"error": "Invalid page number"}), 400

#     per_page = 1000
#     start = (page - 1) * per_page
#     end = start + per_page
#     paginated_data = data[start:end]

#     # Determine if there’s a next page
#     has_more = end < len(data)
#     next_page_url = None

#     if has_more:
#         # Dynamically build full URL for next page
#         base_url = request.base_url  # e.g., http://localhost:5000/items
#         query_params = request.args.to_dict()
#         query_params['page'] = page + 1
#         next_page_url = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in query_params.items())}"

#     return jsonify({
#         "page": page,
#         "per_page": per_page,
#         "total": len(data),
#         "has_more": has_more,
#         "next_page_url": next_page_url,
#         "data": paginated_data
#     })

# # Error handler: Unauthorized
# @app.errorhandler(401)
# def unauthorized(e):
#     return jsonify({"error": str(e)}), 401

# # Error handler: Rate limit exceeded
# @app.errorhandler(429)
# def rate_limit_exceeded(e):
#     return jsonify({"error": "Rate limit exceeded"}), 429

# if __name__ == "__main__":
#     app.run()

from flask import Flask, request, jsonify, abort
import pandas as pd
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Load CSV data once at startup
df = pd.read_csv("sales_pipeline.csv")
data = df.to_dict(orient="records")

app = Flask(__name__)

# API Key from .env or fallback
API_KEY = os.getenv("API_KEY", "default-fallback-token")

# Rate limiter (100 requests/hour/IP)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per hour"]
)

# Auth for /items only
@app.before_request
def check_auth():
    if request.endpoint == "get_items":
        token = request.headers.get("Authorization")
        if token != f"Bearer {API_KEY}":
            abort(401, description="Unauthorized")

@app.route("/items")
def get_items():
    try:
        page = int(request.args.get("page", 1))
        if page < 1:
            raise ValueError
    except ValueError:
        return jsonify({"error": "Invalid page number"}), 400

    # Optional query parameters
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    include_nulls = request.args.get("include_nulls", "false").lower() == "true"

    # Filtering based on engage_date
    filtered_data = []
    for row in data:
        engage_date = row.get("engage_date")
        ##include nulls
       if engage_date is None or str(engage_date).strip() == "" or str(engage_date).strip().lower() == "nan":
            if include_nulls:
                filtered_data.append(row)
            continue

        # Apply date range if specified
        if start_date and end_date:
            try:
                engage_dt = datetime.strptime(engage_date, "%Y-%m-%d")
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                if start_dt <= engage_dt <= end_dt:
                    filtered_data.append(row)
            except Exception as e:
                continue  # Skip if date parsing fails
        elif not start_date and not end_date and not include_nulls:
            # No filtering – load all non-null rows
            filtered_data.append(row)

    # Paginate
    per_page = 1000
    start = (page - 1) * per_page
    end = start + per_page
    paginated_data = filtered_data[start:end]

    has_more = end < len(filtered_data)
    next_page_url = None
    if has_more:
        base_url = request.base_url
        query_params = request.args.to_dict()
        query_params['page'] = page + 1
        next_page_url = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in query_params.items())}"

    return jsonify({
        "page": page,
        "per_page": per_page,
        "total": len(filtered_data),
        "has_more": has_more,
        "next_page_url": next_page_url,
        "data": paginated_data
    })

# Error: Unauthorized
@app.errorhandler(401)
def unauthorized(e):
    return jsonify({"error": str(e)}), 401

# Error: Rate limit
@app.errorhandler(429)
def rate_limit_exceeded(e):
    return jsonify({"error": "Rate limit exceeded"}), 429

if __name__ == "__main__":
    app.run()


