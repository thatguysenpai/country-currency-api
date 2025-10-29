# app/schemas.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CountryCurrencyBase(BaseModel):
    name: str
    capital: Optional[str] = None
    region: Optional[str] = None
    population: int
    currency_code: str
    exchange_rate: Optional[float] = None
    estimated_gdp: Optional[float] = None
    flag_url: Optional[str] = None
    last_refreshed_at: Optional[datetime]


class CountryCurrencyCreate(CountryCurrencyBase):
    pass

class CountryCurrencyResponse(CountryCurrencyBase):
    id: int


    class Config:
        from_attributes = True
        
    
