from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from loader import db


async def get_user_orders(number):
    orders = await db.get_orders_by_phone(number)
    user_orders = InlineKeyboardBuilder()
    for order in orders:
        user_orders.add(InlineKeyboardButton(text=str(order[1]), callback_data=str(order[0])))
    user_orders.add(InlineKeyboardButton(text="🔙 Oynani yopish", callback_data='back'))
    return user_orders.adjust(2).as_markup()


order_keyboards = InlineKeyboardBuilder(
    markup=[
        [
            InlineKeyboardButton(text="💵 To'lo'v qilish", callback_data='payment'),
            InlineKeyboardButton(text='🔙 Oynani yopish', callback_data='back')
        ]
    ]
).adjust(2).as_markup()

order_save_button = InlineKeyboardBuilder(
    markup=[
        [
            InlineKeyboardButton(text="✅ Saqlash", callback_data='save_product'),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data='cancel_product')
        ]
    ]
).adjust(2).as_markup()
