from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from loader import db

async def get_orders(tg_id: int):
    orders = await db.get_orders_by_tg_id(tg_id)
    orders_keyboard = InlineKeyboardBuilder()
    for order in orders:
        orders_keyboard.add(InlineKeyboardButton(text=str(order[1]), callback_data=str(order[0])))
    orders_keyboard.add(InlineKeyboardButton(text="🔙 Oynani yopish", callback_data='back'))
    return orders_keyboard.adjust(2).as_markup()


user_order_keyboard = InlineKeyboardBuilder(
    markup=[
        [
            InlineKeyboardButton(text="💰📝 To'lo'vlar ma'lumotini olish", callback_data='get_payment_info'),
            InlineKeyboardButton(text='🔙 Oynani yopish', callback_data='back')
        ]
    ]
).adjust(2).as_markup()

