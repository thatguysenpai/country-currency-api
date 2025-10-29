from sqlalchemy import Column, Integer, String, Float, DateTime
from app.database import Base

class CountryCurrency(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    capital = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    population = Column(Integer, nullable=True)

    # ✅ make these nullable so they don’t crash when missing
    currency_code = Column(String(10), nullable=True)
    exchange_rate = Column(Float, nullable=True)
    estimated_gdp = Column(Float, nullable=True)

    flag_url = Column(String(255), nullable=True)
    last_refreshed_at = Column(DateTime, nullable=True)
