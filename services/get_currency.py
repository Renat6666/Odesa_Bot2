import requests
from typing import Optional, Dict

def get_currency_rate(ccy: str = "USD") -> Optional[Dict[str, str]]:
    url = "https://api.privatbank.ua/p24api/pubinfo?json&exchange&coursid=5"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        for item in data:
            if item["ccy"] == ccy.upper():
                return {
                    "currency": ccy.upper(),
                    "rate": item["buy"],
                }
        return None
    except requests.RequestException as e:
        print(f"Помилка при запиті: {e}")
        return None