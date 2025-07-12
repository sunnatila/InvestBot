from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton


add_info_button = InlineKeyboardBuilder(
    markup=[
        [
            InlineKeyboardButton(text="➕📝 Kredit qo'shish", callback_data='add_credit'),
            InlineKeyboardButton(text="➕📝 Mavjud mijozga kredit qo'shish", callback_data='add_credit_to_existing_client'),
            InlineKeyboardButton(text="🛠️ Mahsulot turlarini boshqarish", callback_data='products'),
            InlineKeyboardButton(text="📝 Kreditlarni boshqarish", callback_data='edit_info')
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


add_order_button = InlineKeyboardBuilder(
    markup=[
        [
            InlineKeyboardButton(text="✅ Qo'shish", callback_data='add_order'),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data='cancel_order')
        ]
    ]
).adjust(2).as_markup()

