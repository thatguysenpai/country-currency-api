import requests

def fetch_country_data():
    url = "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
    response = requests.get(url, timeout=15)
    if response.status_code != 200:
        raise Exception("Failed to fetch country data")
    return response.json()

def fetch_exchange_rates():
    url = "https://open.er-api.com/v6/latest/USD"
    response = requests.get(url, timeout=15)
    if response.status_code != 200:
        raise Exception("Failed to fetch exchange rates")
    return response.json()
