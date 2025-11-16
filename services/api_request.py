import os
import requests
from dotenv import load_dotenv

load_dotenv()

def api_request(
    limit: int = 3,
    offset: int = 0,
    district_id: list[int] = None,
    microarea_id: list[int] = None,
    street_id: list[int] = None,
    condition_in: list[int] = None,
    rooms_in: list[int] = None,
    price_min: int = None,
    price_max: int = None,
    area_min: int = None,
    area_max: int = None,
    floor_min: int = None,
    floor_max: int = None,
    floors_total_max: int = None,
    lat: float = None,
    lon: float = None,
    radius_km: float = None,
    
    sort: str = "price_desc",

):
    url = os.getenv("API_URL")
    key = os.getenv("API_KEY")

    payload = {"key": key, "section": "secondary"}

    if limit is not None:
        payload["limit"] = limit
    if offset is not None:
        payload["offset"] = offset
    if district_id is not None:
        payload["district_id"] = district_id
    if rooms_in is not None:
        payload["rooms_in"] = rooms_in
    if price_min is not None:
        payload["price_min"] = price_min
    if price_max is not None:
        payload["price_max"] = price_max
    if sort is not None:
        payload["sort"] = sort
    if district_id is not None:
        payload["district_id"] = district_id
    if microarea_id is not None:
        payload["microarea_id"] = microarea_id
    if street_id is not None:
        payload["street_id"] = street_id
    if condition_in is not None:
        payload["condition_in"] = condition_in
    if rooms_in is not None:
        payload["rooms_in"] = rooms_in
    if price_min is not None:
        payload["price_min"] = price_min
    if price_max is not None:
        payload["price_max"] = price_max
    if area_min is not None:
        payload["area_min"] = area_min
    if area_max is not None:
        payload["area_max"] = area_max
    if floor_min is not None:
        payload["floor_min"] = floor_min
    if floor_max is not None:
        payload["floor_max"] = floor_max
    if floors_total_max is not None:
        payload["floors_total_max"] = floors_total_max
    if lat is not None:
        payload["lat"] = lat
    if lon is not None:
        payload["lon"] = lon
    if radius_km is not None:
        payload["radius_km"] = radius_km

    headers = {"Content-Type": "application/json"}

    try:
        verify_ssl = False
        response = requests.post(url, json=payload, headers=headers, verify=verify_ssl, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Помилка запиту: {e}")
        return None

if __name__ == "__main__":
    result = api_request(
        limit=3,
        offset=0,
        district_id=[8],
        price_max=40000,

    )
    print(result)
