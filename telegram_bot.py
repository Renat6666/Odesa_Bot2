import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart
from dotenv import load_dotenv
from aiogram import types

from services.db_func import (
    get_or_create_user,
    save_message,
    save_reply,
    update_user_last_active,
    update_user_contact,
    update_user,
    get_user_data,
    clear_context
)
from services.chat_func import (
    chat,
    chat_tracker,
    req_rieltor_tracker,
    process_apartment_search,
    appartment_request_data
)
from services.keyboards import get_contact_keyboard, remove_keyboard
from services.save_to_spreadsheet import save_to_spreadsheet

load_dotenv()

async def start_command(message: Message):
    await get_or_create_user(message.from_user.id)
    clear_context_res = await clear_context(message.from_user.id)
    
    msg_id = await save_message(message.from_user.id, "")
    await message.answer("Вітаю вас у світі нерухомості без стресу! Я — ШІ-РІЕЛТОР.")
    await message.answer("Як до вас можна звертатися?")
    await save_reply(msg_id, "Вітаю вас у світі нерухомості без стресу! Я — ШІ-РІЕЛТОР.")
    await save_reply(msg_id, "Як до вас можна звертатися?")
    await update_user_last_active(message.from_user.id)


async def handle_message(message: Message):
    await get_or_create_user(message.from_user.id)
    await update_user_last_active(message.from_user.id)
    msg_id = await save_message(message.from_user.id, message.text or "")
    
    try:
        await message.bot.send_chat_action(message.chat.id, types.ChatAction.TYPING)
    except Exception:
        pass
    
    try:
        # Виконуємо обидва запити до нейромережі одночасно
        tracker, req_rieltor = await asyncio.gather(
            chat_tracker(message.from_user.id),
            req_rieltor_tracker(message.text)
        )
        if req_rieltor:
            await message.answer("Дякую! Обробляю ваш запит...  зачекайте⏳")
            await save_reply(msg_id, "Дякую! Обробляю ваш запит...  зачекайте⏳")
            username = message.from_user.username or ""
            user_id = message.from_user.id
            await update_user_contact(user_id, username)
            data = await appartment_request_data(user_id)
            await update_user(user_id, data)
            data_to_send = await get_user_data(user_id)
            print(f"Data to send for user {user_id}: {data_to_send}")
            started_at = data_to_send["started_at"].strftime("%Y-%m-%d %H:%M:%S")
            started_at = str(started_at)
            last_action = data_to_send["last_action"].strftime("%Y-%m-%d %H:%M:%S")
            last_action = str(last_action)
            result = await save_to_spreadsheet(user_id, data_to_send["username"], "ua", started_at, last_action, data_to_send["lead"], data_to_send["avg_budget"], data_to_send["reason_decline"], data_to_send["response_time"])
            await message.answer("З вами зв'яжеться наш ріелтор в будні дні з 9:00 до 18:00")
            await save_reply(msg_id, "З вами зв'яжеться наш ріелтор в будні дні з 9:00 до 18:00")
            return

            
            
        if tracker:
            # Діалог завершено, просимо контакт
            response_text = (
                "Чудово! Я зібрав всю необхідну інформацію. 🎯\n\n"
                "Для пошуку квартири, будь ласка, поділіться своїм номером телефону."
            )
            await message.answer(response_text, reply_markup=get_contact_keyboard())
            await save_reply(msg_id, response_text)
            return  # Чекаємо на контакт від користувача

        # Продовжуємо діалог
        response = await chat(message.from_user.id)
        if not response:
            await message.answer("Вибачте, виникла технічна помилка. Спробуйте ще раз.")
            await save_reply(msg_id, "Технічна помилка")
            return
            
        await message.answer(response)
        await save_reply(msg_id, response)
    except Exception as e:
        await message.answer(f"Помилка аналізу: {e}")
        await save_reply(msg_id, f"Помилка аналізу: {e}")


async def handle_contact_message(message: Message):
    """Обробник для повідомлень з контактом"""
    await get_or_create_user(message.from_user.id)
    await update_user_last_active(message.from_user.id)
    
    if not message.contact:
        await message.answer(
            "Будь ласка, поділіться контактом, натиснувши кнопку нижче.",
            reply_markup=get_contact_keyboard()
        )
        return
    
    contact = message.contact
    user_id = message.from_user.id
    
    # Перевіряємо, чи користувач поділився своїм контактом
    if contact.user_id != user_id:
        await message.answer(
            "Будь ласка, поділіться саме вашим контактом, натиснувши кнопку нижче.",
            reply_markup=get_contact_keyboard()
        )
        return
    
    await message.answer(
        "Дякую! Обробляю ваш запит... ⏳",
        reply_markup=remove_keyboard()
    )
    
    try:
        await message.bot.send_chat_action(message.chat.id, types.ChatAction.TYPING)
    except Exception:
        pass

    try:
        # Отримуємо дані контакту
        phone = contact.phone_number or None
        # Username беремо з from_user, оскільки Contact не має цього атрибуту
        username = message.from_user.username or ""
        
        await update_user_contact(user_id, username)
        
        # Обробляємо пошук квартир
        result = await process_apartment_search(user_id, phone)
        
        if not result:
            await message.answer(
                "Вибачте, виникла помилка при обробці запиту. Спробуйте пізніше."
            )
            return
        
        apartments = result.get("apartments", [])
        total_count = result.get("total_count", 0)
        
        if not apartments:
            await message.answer(
                "На жаль, за вашими параметрами не знайдено квартир. "
                "Спробуймо розширити критерії пошуку?"
            )
            return
            
        await message.answer(
            f"🎉 Чудово! Знайдено {total_count} варіантів.\n"
            f"Ось найкращі 3 квартири для вас:"
        )
        
        for idx, apartment in enumerate(apartments, 1):
            photos = apartment.get("photos", [])
            text = apartment.get("text", "")
            
            # Відправляємо фото, якщо вони є
            if photos:
                from aiogram.types import InputMediaPhoto
                media_group = [InputMediaPhoto(media=url) for url in photos]
                try:
                    await message.answer_media_group(media=media_group)
                    await asyncio.sleep(0.3)
                except Exception as e:
                    print(f"Error sending photos: {e}")
            
            # Відправляємо опис квартири
            await message.answer(f"━━━ Варіант {idx} ━━━\n\n{text}")
            await asyncio.sleep(0.5)
        
        # Пропонуємо більше варіантів
        if total_count > 3:
            remaining = total_count - 3
            await message.answer(
                f"\n💬 У мене є ще {remaining} варіантів за вашими параметрами!\n\n"
                f"Якщо хочете побачити більше об'єктів або змінити параметри пошуку чи звязатись з ріелтором - просто напишіть мені."
            )
        else:
            await message.answer(
                "\n💬 Це всі доступні варіанти за вашими параметрами.\n\n"
                "Якщо хочете змінити критерії пошуку чи звязатись з ріелтором - просто напишіть мені!"
            )
    except Exception as e:
        print(f"Error in handle_contact_message: {e}")
        await message.answer(f"Помилка при обробці запиту: {e}")





async def main():
    bot = Bot(token=os.getenv("TG_BOT_TOKEN"))
    dp = Dispatcher()
    
    # Реєструємо обробники
    dp.message.register(start_command, CommandStart())
    # Обробник контактів повинен бути ПЕРЕД загальним обробником повідомлень
    dp.message.register(handle_contact_message, lambda msg: msg.contact is not None)
    dp.message.register(handle_message) 
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception:
        pass
    
    print("🤖 Bot started. Polling updates...")

    
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())