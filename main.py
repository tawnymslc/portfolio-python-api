from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # local
        "https://tawny-mathi.com",   # production
        "https://www.tawny-mathi.com" 
    ], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------
# PROJECT ETL DASHBOARD - EXTRACT, TRANSFORM, LOAD
# ---------------------

# ---------------------
# RAW
# ---------------------
@app.get("/products/raw")
def get_raw_products():
    try:
        response = requests.get("https://dummyjson.com/products?limit=3")
        return response.json()["products"]
    except Exception as e:
        return { "error": str(e) }

@app.get("/products/average-prices")
def get_average_prices():
    try:
        # ---------------------
        # EXTRACT
        # ---------------------
        response = requests.get("https://dummyjson.com/products?limit=100")
        data = response.json()["products"]

        # ---------------------
        # TRANSFORM
        # ---------------------
        grouped = {}
        for product in data:
            category = product["category"]
            if category not in grouped:
                grouped[category] = { "total": 0, "count": 0,  "minPrice": product["price"] }

            grouped[category]["total"] += product["price"]
            grouped[category]["count"] += 1
            grouped[category]["minPrice"] = min(
                grouped[category]["minPrice"],
                product["price"]
            )

        # ---------------------
        # LOAD
        # ---------------------
        result = []
        for category, values in grouped.items():
            avg = round(values["total"] / values["count"], 2)
            result.append({ 
                "category": category, 
                "averagePrice": avg, 
                "count": values["count"],
                "minPrice": values["minPrice"]
                })

        return result

    except Exception as e:
        return { "error": str(e) }

# ---------------------
# PROJECT API DATA SYNC - Integrate data from another system to our systems
# ---------------------

destination_db = []
imported_ids = set()

# ---------------------
# SOURCE SYSTEM
# ---------------------
SOURCE_URL = "https://jsonplaceholder.typicode.com/users"

def fetch_deals():
    response = requests.get(SOURCE_URL, timeout=20)
    response.raise_for_status()
    return response.json()

def transform_borrower(borrower: dict) -> dict:
    return {
        "dealId": borrower["id"],

        # lifecycle status (owned by your system)
        "status": "conditionallyApproved",

        # borrower section
        "borrower": {
            "fullName": borrower["name"],
            "username": borrower["username"],
            "email": borrower["email"],
            "city": borrower["address"]["city"],
            "lat": borrower["address"]["geo"]["lat"],
            "lng": borrower["address"]["geo"]["lng"],
        },

        # business section
        "business": {
            "companyName": borrower["company"]["name"]
        }
    }

# ---------------------
# DESTINATION SYSTEM
# ---------------------
@app.post("/import-deals")
def import_deals(deals: list[dict]):
    added = 0

    for d in deals:
        did = d.get("dealId")
        if did is None:
            continue

        if did not in imported_ids:
            imported_ids.add(did)
            destination_db.append(d)
            added += 1

    return {"imported": added, "received": len(deals)}

# ---------------------
# SYNC ACTION
# ---------------------
@app.get("/sync-deals")
def sync_deals():
    raw = fetch_deals()
    cleaned = [transform_borrower(b) for b in raw]

    # push into destination system by calling our own ingest function
    # (keeps the "integration" story: import endpoint is the destination contract)
    result = import_deals(cleaned)

    return {
        "source_count": len(raw),
        "transformed_count": len(cleaned),
        **result
    }

@app.get("/deals")
def get_deals():
    return destination_db