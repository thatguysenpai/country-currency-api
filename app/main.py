# app/main.py
import requests
import random
from datetime import datetime, timezone
import os

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import engine, get_db
from app.utils import fetch_country_data, fetch_exchange_rates
from PIL import Image, ImageDraw, ImageFont

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Country Currency API")


def error_503(api_name: str, details: str = ""):
    return HTTPException(
        status_code=503,
        detail={"error": "External data source unavailable", "details": f"Could not fetch data from {api_name}. {details}"},
    )


def error_400(detail_map: dict):
    return JSONResponse(status_code=400, content={"error": "Validation failed", "details": detail_map})


def error_404(msg: str = "Country not found"):
    return HTTPException(status_code=404, detail={"error": msg})


@app.get("/")
def root():
    return {"message": "Country Currency API is running"}


# --- CRUD + filtering ---
@app.get("/countries")
def get_countries(region: str = None, currency: str = None, sort: str = None, db: Session = Depends(get_db)):
    q = db.query(models.CountryCurrency)
    if region:
        q = q.filter(models.CountryCurrency.region.ilike(region))
    if currency:
        q = q.filter(models.CountryCurrency.currency_code.ilike(currency))
    if sort == "gdp_desc":
        q = q.order_by(models.CountryCurrency.estimated_gdp.desc())
    elif sort == "gdp_asc":
        q = q.order_by(models.CountryCurrency.estimated_gdp.asc())
    return q.all()


@app.get("/countries/{country_name}")
def get_country(country_name: str, db: Session = Depends(get_db)):
    record = db.query(models.CountryCurrency).filter(models.CountryCurrency.name.ilike(country_name)).first()
    if not record:
        raise error_404()
    return record


@app.post("/countries", response_model=schemas.CountryCurrencyResponse)
def add_country(data: schemas.CountryCurrencyCreate, db: Session = Depends(get_db)):
    try:
        new_country = models.CountryCurrency(**data.dict())
    except Exception as e:
        return error_400({"schema": str(e)})
    db.add(new_country)
    db.commit()
    db.refresh(new_country)
    return new_country


@app.put("/countries/{country_name}")
def update_country(country_name: str, exchange_rate: float, db: Session = Depends(get_db)):
    record = db.query(models.CountryCurrency).filter(models.CountryCurrency.name.ilike(country_name)).first()
    if not record:
        raise error_404()
    record.exchange_rate = exchange_rate
    db.commit()
    db.refresh(record)
    return record


@app.delete("/countries/{country_name}")
def delete_country(country_name: str, db: Session = Depends(get_db)):
    record = db.query(models.CountryCurrency).filter(models.CountryCurrency.name.ilike(country_name)).first()
    if not record:
        raise error_404()
    db.delete(record)
    db.commit()
    return {"message": f"{country_name} deleted successfully"}


# --- Status endpoint ---
@app.get("/status")
def get_status(db: Session = Depends(get_db)):
    total = db.query(models.CountryCurrency).count()
    ts_path = "cache/last_refreshed.txt"
    last_refreshed = None
    if os.path.exists(ts_path):
        with open(ts_path) as f:
            last_refreshed = f.read().strip()
    return {"total_countries": total, "last_refreshed_at": last_refreshed}


@app.get("/countries/{name}")
def get_country(name: str, db: Session = Depends(get_db)):
    record = db.query(models.CountryCurrency).filter(models.CountryCurrency.name.ilike(name)).first()
    if not record:
        raise error_404()
    return record


# --- Refresh endpoint ---
@app.post("/countries/refresh")
def refresh_countries(db: Session = Depends(get_db)):
    try:
        countries_resp = requests.get(
            "https://restcountries.com/v3.1/all?fields=name,capital,region,population,flags,currencies",
            timeout=20,
        )
        countries_resp.raise_for_status()
    except Exception as e:
        raise error_503("Countries API", str(e))

    try:
        rates_resp = requests.get("https://open.er-api.com/v6/latest/USD", timeout=20)
        rates_resp.raise_for_status()
    except Exception as e:
        raise error_503("Exchange Rates API", str(e))

    try:
        countries = countries_resp.json()
    except Exception:
        countries = []

    try:
        rates_payload = rates_resp.json()
    except Exception:
        rates_payload = {}
    rates = rates_payload.get("rates", {})

    if isinstance(countries, dict) and "data" in countries:
        countries = countries["data"]
    if not isinstance(countries, list):
        countries = []

    refresh_ts = datetime.now(timezone.utc)

    try:
        for c in countries:
            if not isinstance(c, dict):
                continue

            name = (c.get("name") or {}).get("common")
            if not name:
                continue

            capital = (c.get("capital") or [None])[0]
            region = c.get("region")
            population = c.get("population") or 0

            currencies = c.get("currencies") or {}
            if isinstance(currencies, dict) and len(currencies) > 0:
                currency_code = next(iter(currencies))
            else:
                currency_code = None

            if currency_code is None:
                exchange_rate = None
                estimated_gdp = 0.0
            else:
                rate_val = rates.get(currency_code)
                if rate_val is None:
                    exchange_rate = None
                    estimated_gdp = None
                else:
                    try:
                        exchange_rate = float(rate_val)
                    except Exception:
                        exchange_rate = None

                    if exchange_rate and population:
                        multiplier = random.randint(1000, 2000)
                        estimated_gdp = (population * multiplier) / exchange_rate
                    else:
                        estimated_gdp = None

            flag_url = (c.get("flags") or {}).get("svg")

            existing = db.query(models.CountryCurrency).filter(models.CountryCurrency.name.ilike(name)).first()
            if existing:
                existing.capital = capital
                existing.region = region
                existing.population = population
                existing.currency_code = currency_code
                existing.exchange_rate = exchange_rate
                existing.estimated_gdp = estimated_gdp
                existing.flag_url = flag_url
                existing.last_refreshed_at = refresh_ts
            else:
                new_row = models.CountryCurrency(
                    name=name,
                    capital=capital,
                    region=region,
                    population=population,
                    currency_code=currency_code,
                    exchange_rate=exchange_rate,
                    estimated_gdp=estimated_gdp,
                    flag_url=flag_url,
                    last_refreshed_at=refresh_ts,
                )
                db.add(new_row)

        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"error": "Internal server error", "details": str(e)})

    try:
        os.makedirs("cache", exist_ok=True)
        with open("cache/last_refreshed.txt", "w") as f:
            f.write(refresh_ts.isoformat())
    except Exception:
        pass

    try:
        total = db.query(models.CountryCurrency).count()
        top5 = (
            db.query(models.CountryCurrency)
            .filter(models.CountryCurrency.estimated_gdp.isnot(None))
            .order_by(models.CountryCurrency.estimated_gdp.desc())
            .limit(5)
            .all()
        )

        img_w, img_h = 1000, 500
        im = Image.new("RGB", (img_w, img_h), color=(255, 255, 255))
        draw = ImageDraw.Draw(im)
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", 18)
        except Exception:
            font = ImageFont.load_default()

        y = 20
        draw.text((20, y), f"Summary (Last refreshed: {refresh_ts.isoformat()})", font=font, fill=(0, 0, 0))
        y += 30
        draw.text((20, y), f"Total countries: {total}", font=font, fill=(0, 0, 0))
        y += 40
        draw.text((20, y), "Top 5 by estimated GDP:", font=font, fill=(0, 0, 0))
        y += 26

        for idx, r in enumerate(top5, start=1):
            gdp_text = f"{r.estimated_gdp:,.2f}" if r.estimated_gdp else "N/A"
            draw.text((40, y), f"{idx}. {r.name}: {gdp_text}", font=font, fill=(0, 0, 0))
            y += 22

        os.makedirs("cache", exist_ok=True)
        im.save("cache/summary.png")
    except Exception:
        pass

    return {"message": "Refresh complete", "total_processed": len(countries), "last_refreshed_at": refresh_ts.isoformat()}


# --- Serve summary image ---
@app.get("/countries/image")
def get_summary_image():
    path = os.path.join("cache", "summary.png")
    if not os.path.exists(path):
        return JSONResponse(status_code=404, content={"error": "Summary image not found"})
    return FileResponse(path, media_type="image/png", filename="summary.png")
