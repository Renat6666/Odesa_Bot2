from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def get_contact_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📞 Поділитись контактом",
                    request_contact=True
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Натисніть кнопку, щоб поділитися контактом"
    )
    return keyboard


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
