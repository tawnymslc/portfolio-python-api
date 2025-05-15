# ETL Dashboard Backend (FastAPI)

This Python backend powers the ETL Dashboard feature on my portfolio site. It extracts live product data from an external API, transforms the data by grouping and averaging prices by category, and serves both the raw and aggregated data to the frontend for visualization.

---

## 🔧 Features

- **Extracts** product data from [`dummyjson.com/products`](https://dummyjson.com/products)
- **Transforms** raw JSON by calculating average price per product category
- **Loads** data into frontend via two clean API endpoints
- Built with **FastAPI**, a high-performance web framework for building APIs with Python

---

## 🚀 API Endpoints

- `GET /products/raw`  
  Returns the raw product data as received from the external API

- `GET /products/average-prices`  
  Returns transformed data: average price per category, calculated on the server

---

## ⚙️ Technologies

- Python
- FastAPI
- Uvicorn (for local dev server)
- Requests (for external API consumption)
- CORS Middleware

---

## 🧪 Local Development

1. Create a virtual environment  
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
