from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # local
        "https://tawny-mathi.com",   # production
        "https://www.tawny-mathi.com" # cors
    ], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Extracted (raw) data
@app.get("/products/raw")
def get_raw_products():
    try:
        response = requests.get("https://dummyjson.com/products?limit=100")
        return response.json()["products"]
    except Exception as e:
        return { "error": str(e) }

@app.get("/products/average-prices")
def get_average_prices():
    try:
        # 1. Extract
        response = requests.get("https://dummyjson.com/products?limit=100")
        data = response.json()["products"]

        # 2. Transform
        grouped = {}
        for product in data:
            category = product["category"]
            if category not in grouped:
                grouped[category] = { "total": 0, "count": 0 }

            grouped[category]["total"] += product["price"]
            grouped[category]["count"] += 1

        # 3. Load into simplified output
        result = []
        for category, values in grouped.items():
            avg = round(values["total"] / values["count"], 2)
            result.append({ "category": category, "averagePrice": avg })

        return result

    except Exception as e:
        return { "error": str(e) }