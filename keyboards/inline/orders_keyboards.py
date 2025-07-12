from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from loader import db


async def get_user_orders(number):
    orders = await db.get_orders_by_phone(number)
    user_orders = InlineKeyboardBuilder()
    for order in orders:
        user_orders.add(InlineKeyboardButton(text=str(order[4]), callback_data=str(order[0])))
    user_orders.add(InlineKeyboardButton(text="🔙 Oynani yopish", callback_data='back'))
    return user_orders.adjust(2).as_markup()


order_keyboards = InlineKeyboardBuilder(
    markup=[
        [
            InlineKeyboardButton(text="💵 Yarim to'lo'v qilish", callback_data='part_payment'),
            InlineKeyboardButton(text="💵 Oylik To'lo'v qilish", callback_data='monthly_payment'),
            InlineKeyboardButton(text="💵 To'liq To'lo'v qilish", callback_data='full_payment'),
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



async def get_users():
    users = await db.get_users()
    users_keyboard = InlineKeyboardBuilder()
    for user in users:
        users_keyboard.add(InlineKeyboardButton(text=str(user[1]), callback_data=str(user[0])))
    users_keyboard.add(InlineKeyboardButton(text="🔙 Oynani yopish", callback_data='back'))
    return users_keyboard.adjust(2).as_markup()
