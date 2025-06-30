from fastapi import FastAPI, Query
import pandas as pd
from fastapi.responses import JSONResponse

app = FastAPI()

# Load CSV file instead of Excel
df = pd.read_csv("sales_pipeline.csv")
df.fillna("", inplace=True)

@app.get("/api/data")
def get_data(page: int = Query(1, ge=1), limit: int = Query(100, le=1000)):
    start = (page - 1) * limit
    end = start + limit
    total = len(df)
    data = df.iloc[start:end].to_dict(orient="records")

    return {
        "page": page,
        "limit": limit,
        "total_records": total,
        "data": data
    }

    return {
        "page": page,
        "limit": limit,
        "total_records": total,
        "data": data
    }
