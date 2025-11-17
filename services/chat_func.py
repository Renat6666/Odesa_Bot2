from services.prompts.chat_tracker import get_chat_tracker
from services.prompts.chat_data import get_chat_data
from services.prompts.chat_instruction import get_chat_instruction
from services.prompts.req_rieltor import req_rieltor
from services.prompts.appartment_request import get_appartment_request_prompt
from aiogram import types
from aiogram.types import Message
import asyncio
import json
import re

from services.ai_req import gemini_request
from services.db_func import save_api_data
from services.keyboards import get_contact_keyboard, remove_keyboard
from services.api_request import api_request


def clean_json_response(response: str) -> dict:
    """
    Очищає відповідь від AI та конвертує у JSON.
    Видаляє markdown обгортки типу ```json ... ```
    """
    if not response:
        return None
    
    # Видаляємо markdown блоки коду
    # Шукаємо ```json ... ``` або ``` ... ```
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response)
    if json_match:
        response = json_match.group(1)
    
    # Видаляємо зайві пробіли
    response = response.strip()
    
    try:
        # Парсимо JSON
        data = json.loads(response)
        return data
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Response was: {response}")
        return None


async def chat_tracker(user_id: int):
    prompt = await get_chat_tracker(user_id)
    response = await gemini_request(prompt)
    if response == "True":
        print(f"Chat tracker for user {user_id}: True")
        return True
    else:
        print(f"Chat tracker for user {user_id}: False")
        return False


async def chat(user_id: int):
    prompt = await get_chat_instruction(user_id)
    response = await gemini_request(prompt)
    print(f"AI response for user {user_id}: ", response)
    return response


async def chat_data(user_id: int):
    prompt = await get_chat_data(user_id)
    response = await gemini_request(prompt)
    print(f"Chat data for user {user_id}: ", response)
    
    # Очищаємо та парсимо JSON відповідь
    cleaned_data = clean_json_response(response)
    if not cleaned_data:
        print(f"Failed to parse chat data for user {user_id}")
        return None
    
    return cleaned_data


async def appartment_request_data(user_id: int):
    prompt = await get_appartment_request_prompt(user_id)
    response = await gemini_request(prompt)
    print(f"Appartment request data for user {user_id}: ", response)
    
    # Очищаємо та парсимо JSON відповідь
    cleaned_data = clean_json_response(response)
    if not cleaned_data:
        print(f"Failed to parse appartment request data for user {user_id}")
        return None
    
    return cleaned_data


async def req_rieltor_tracker(message: str):
    prompt = req_rieltor(message)  # Без await - функція не async
    response = await gemini_request(prompt)
    if response == "True":
        print(f"Req rieltor tracker for message {message}: True")
        return True
    else:
        print(f"Req rieltor tracker for message {message}: False")
        return False





async def get_api_apartments(data: dict):
    items = data.get("items")
    total_count = data.get("count")
    apartments = []  # Список квартир з фото та описом окремо
    
    for it in items[:3]:
        title = it.get("title") or "Об'єкт нерухомості"
        price = it.get("prices", {}).get("value")
        addr = it.get("address", {})
        street = addr.get("street")
        district = addr.get("district")
        city = addr.get("city")
        area_total = it.get("area_total")
        rooms = it.get("rooms")
        condition = it.get("condition")
        desc = (it.get("description") or "").splitlines()
        short = " ".join(desc[:3])[:400]
        
        # Формуємо текстовий опис БЕЗ фото
        parts = [
            f"🏠 {title}",
            f"\n📍 Місто: {city or '-'}, Район: {district or '-'}, Вулиця: {street or '-'}",
            f"🛏 Кімнат: {rooms or '-'}, Площа: {area_total or '-'} м², Стан: {condition or '-'}",
            f"💰 Ціна: ${int(price) if isinstance(price, (int, float)) else price or '-'}",
            f"📅 Дата оновлення: {it.get('updated_at', '-')}",
        ]
        if short:
            parts.append(f"\n📝 {short}")
        
        text_message = "\n".join(parts)
        
        # Обробка фото окремо
        photo_urls = []
        photos = it.get("photos")
        
        if photos and isinstance(photos, list) and len(photos) > 0:
            try:
                # Якщо photos[0] - рядок JSON, парсимо
                if isinstance(photos[0], str):
                    photos_data = json.loads(photos[0])
                    if isinstance(photos_data, list) and len(photos_data) > 0:
                        # Беремо до 10 перших фото (Telegram ліміт для media group)
                        for photo in photos_data[:10]:
                            # Використовуємо 'url' для відносного шляху
                            photo_url = photo.get('url', '')
                            if photo_url:
                                # Формуємо повний URL
                                full_url = f"https://re24.com.ua/{photo_url}"
                                photo_urls.append(full_url)
                
                # Якщо photos[0] - вже список словників
                elif isinstance(photos[0], dict):
                    for photo in photos[:10]:
                        photo_url = photo.get('url', '')
                        if photo_url:
                            full_url = f"https://re24.com.ua/{photo_url}"
                            photo_urls.append(full_url)
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                print(f"Could not parse photos: {e}")
        
        apartments.append({
            "text": text_message,
            "photos": photo_urls  # Список URL фотографій
        })
    
    return {
        "apartments": apartments,
        "total_count": total_count,
    }
    
    
    
async def process_apartment_search(user_id: int, phone: str):
    """Обробка пошуку квартир без UI логіки"""
    # Отримуємо дані від ШІ
    api_data = await chat_data(user_id)
    if not api_data:
        return None
    
    # Зберігаємо в БД
    await save_api_data(user_id, phone, api_data)
    
    # Робимо запит до API
    response = api_request(**api_data)
    print(f"API response for user {user_id}: ", response)
    
    if not response:
        return None
    
    # Обробляємо результати
    api_apartments = await get_api_apartments(response)
    return {
        "apartments": api_apartments.get("apartments"),
        "total_count": api_apartments.get("total_count"),
    }


if __name__ == "__main__":
    print(asyncio.run(chat_tracker(6628418858)))


    
    


