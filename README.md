# 🌍 Country Data API

A **FastAPI-based RESTful API** that fetches, stores, and manages country data using the [REST Countries API](https://restcountries.com).  
It provides CRUD operations for managing country information and exchange rate data.

---

## 🚀 Features

- Fetches country details such as:
  - **Name**
  - **Capital**
  - **Region**
  - **Population**
  - **Flag**
  - **Currencies**
- Stores data in a **SQLite database**.
- Allows CRUD operations (Create, Read, Update, Delete).
- Includes an endpoint to refresh all country data from the external API.
- Includes exchange rate lookup for each currency.

---

## 🧠 Tech Stack

- **FastAPI** — Web framework  
- **SQLite** — Local database  
- **SQLAlchemy** — ORM for database management  
- **Uvicorn** — ASGI server for running FastAPI  
- **Requests** — For fetching external data  

---

## 🛠️ Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/country-data-api.git
cd country-data-api

```
### 2. Create a Virtual Environment
```




```
### 3. Install Dependencies
```

pip install -r requirements.txt



```
### 4. Run the API
```

uvicorn main:app --reload



```
### 5. Open the Docs
```
http://127.0.0.1:8000/docs




🧩 Example Usage

Fetch Country

> GET /countries/Ghana

Response: 

{
  "name": "Ghana",
  "capital": "Accra",
  "region": "Africa",
  "population": 31072940,
  "flag": "https://flagcdn.com/w320/gh.png",
  "currency": "GHS"
}

