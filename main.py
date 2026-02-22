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
def fetch_users():
    response = requests.get("https://jsonplaceholder.typicode.com/users")
    response.raise_for_status()
    return response.json()
# ---------------------
# TRANSFORM
# ---------------------
def transform_user(user):
    return {
        "userId": user["id"],
        "fullName": user["name"],
        "email": user["email"],
        "city": user["address"]["city"],
        "latitude": user["address"]["geo"]["lat"],
        "companyName": user["company"]["name"]
    }

# ---------------------
# DESTINATION SYSTEM
# ---------------------
@app.post("/import-users")
def import_users(users: list[dict]):
    added = 0

    for u in users:
        uid = u.get("userId")
        if uid is None:
            continue

        if uid not in imported_ids:
            imported_ids.add(uid)
            destination_db.append(u)
            added += 1

    return {"imported": added, "received": len(users)}

# ---------------------
# SYNC ACTION
# ---------------------
@app.get("/sync-users")
def sync_users():
    raw_users = fetch_users()
    cleaned = [transform_user(u) for u in raw_users]

    # push into destination system by calling our own ingest function
    # (keeps the "integration" story: import endpoint is the destination contract)
    result = import_users(cleaned)

    return {
        "source_count": len(raw_users),
        "transformed_count": len(cleaned),
        **result
    }

@app.get("/users")
def get_users():
    return destination_db