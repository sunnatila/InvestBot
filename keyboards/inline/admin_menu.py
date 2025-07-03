from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton


add_info_button = InlineKeyboardBuilder(
    markup=[
        [
            InlineKeyboardButton(text="➕ Ma'lumot qo'shish", callback_data='add_info'),
            InlineKeyboardButton(text="🛠️ Mahsulot turlarini boshqarish", callback_data='products'),
            InlineKeyboardButton(text="🛒 Mahsulotlarni boshqarish", callback_data='edit_info')
        ]
    ]
).adjust(2).as_markup()


product_first_payment = InlineKeyboardBuilder(
    markup=[
        [
            InlineKeyboardButton(text="✅ Mavjud", callback_data='yes'),
            InlineKeyboardButton(text="❌ Mavjud emas", callback_data='no')
        ]
    ]
).adjust(2).as_markup()
