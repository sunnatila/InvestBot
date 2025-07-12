from aiogram.utils.keyboard import KeyboardButton, ReplyKeyboardBuilder


user_keyboard = ReplyKeyboardBuilder(
    markup=[
        [
            KeyboardButton(text="🛒 Mahsulotlarni ko'rish")
        ],
    ]
).adjust(2).as_markup(resize_keyboard=True, one_time_keyboard=True)

