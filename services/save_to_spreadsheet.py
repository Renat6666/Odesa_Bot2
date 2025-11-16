from dotenv import load_dotenv
import os
import gspread
from typing import List, Dict, Optional

load_dotenv()

SAVE_TO_SPREADSHEET_SPREADSHEET = os.getenv("SAVE_TO_SPREADSHEET_SPREADSHEET")
SAVE_TO_SPREADSHEET_GID = os.getenv("SAVE_TO_SPREADSHEET_GID")


def save_to_spreadsheet(
    user_id: int,
    username: str,
    language: str,
    started_at: str,
    last_action: str,
    lead: str,
    avg_budget: float,
    reason_decline: str,
    response_time: float,
):

    try:
        # Авторизація через service account
        gc = gspread.service_account(filename='table_editor.json')
        
        # Відкриваємо таблицю за URL
        sh = gc.open_by_url(SAVE_TO_SPREADSHEET_SPREADSHEET)
        
        # Отримуємо worksheet за GID
        worksheet = sh.get_worksheet_by_id(int(SAVE_TO_SPREADSHEET_GID))
        
        # Підготовка даних для запису
        row = [
            user_id,
            username or '',
            language or '',
            started_at or '',
            last_action or '',
            lead or '',
            avg_budget or 0,
            reason_decline or '',
            response_time or 0,
        ]
        
        # Додаємо новий рядок
        worksheet.append_row(row)
        print(f"Successfully saved data for user {user_id}")
        return True
        
    except Exception as e:
        print(f"Error saving to spreadsheet: {e}")
        return False