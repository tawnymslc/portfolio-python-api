from fastapi import FastAPI, HTTPException
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
# PROJECT: LENDER API INTEGRATION SIMULATOR
# Simulates how a lender retrieves deal data from a partner API,
# transforms the response into its internal LOS schema,
# and imports records into the lender system.
# ---------------------

deals_db = []
imported_ids = set()

# ---------------------
# SYS A / PARTNER API SOURCE (LENDIO-LIKE)
# Simulates the partner system that provides raw deal data
# to lenders through an API.
# ---------------------
SOURCE_URL = "https://jsonplaceholder.typicode.com/users"

def fetch_deals():
    response = requests.get(SOURCE_URL, timeout=20)
    response.raise_for_status()
    return response.json()

# ---------------------
# SYS A / PARTNER API GET DEAL BY ID
# Simulates a lender calling the partner API to retrieve
# a single raw deal response by ID.
# ---------------------
@app.get("/deals/{deal_id}")
def get_deal_by_id(deal_id: int):
    raw = fetch_deals()
    match = next((d for d in raw if d["id"] == deal_id), None)

    if not match:
        raise HTTPException(status_code=404, detail="Deal not found in source")

    return match


# ---------------------
# SYS B / INTEGRATION MAPPING LAYER
# Transforms raw partner API deal data into the lender's
# internal LOS schema before import.
# ---------------------
def transform_deal(deal: dict) -> dict:
    return {
        "dealId": deal["id"],

        # lifecycle status (owned by your system)
        "status": "conditionallyApproved",

        # borrower section
        "borrower": {
            "fullName": deal["name"],
            "username": deal["username"],
            "email": deal["email"],
            "city": deal["address"]["city"],
            "lat": deal["address"]["geo"]["lat"],
            "lng": deal["address"]["geo"]["lng"],
        },

        # business section
        "business": {
            "companyName": deal["company"]["name"]
        }
    }

# ---------------------
# SYS B / LENDER SYNC WORKFLOW
# Simulates the lender retrieving deals from the partner API,
# transforming them into the LOS schema,
# and sending them to the lender import endpoint.
# ---------------------
@app.post("/sync-deals")
def sync_deal():
    raw = fetch_deals()
    cleaned = [transform_deal(d) for d in raw]

    # push into destination system by calling our own ingest function
    # (keeps the "integration" story: import endpoint is the destination contract)
    result = import_deal(cleaned)

    return {
        "source_count": len(raw),
        "transformed_count": len(cleaned),
        **result
    }

# ---------------------
# SYS C / LENDER LOS IMPORT ENDPOINT
# Receives transformed deals from the integration layer
# and imports them into the lender's internal system.
# Prevents duplicate imports by deal ID.
# ---------------------
@app.post("/lender/import-deals")
def import_deal(deals: list[dict]):
    added = 0

    for d in deals:
        did = d.get("dealId")
        if did is None:
            continue

        if did not in imported_ids:
            imported_ids.add(did)
            deals_db.append(d)
            added += 1

    return {"imported": added, "received": len(deals)}

# ---------------------
# SYS C / LENDER LOS STORED DEALS
# Returns deals that have already been imported
# into the lender's internal system.
# ---------------------
@app.get("/lender-deals")
def get_deals():
    return deals_db
