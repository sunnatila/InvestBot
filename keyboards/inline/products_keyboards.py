from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from loader import db

product_keyboard = InlineKeyboardBuilder(
    markup=[
        [
            InlineKeyboardButton(text="➕ Mahsulot turi qo'shish", callback_data='add_pr_type'),
            InlineKeyboardButton(text="🗑️ Mahsulot turini o'chirish", callback_data='del_pr_type'),
            InlineKeyboardButton(text="🔙 Oynani yopish", callback_data='back')
        ]
    ]
).adjust(2).as_markup()


async def get_product_types():
    product_types_db = await db.get_product_types()
    if product_types_db:
        product_types = InlineKeyboardBuilder()
        for type in product_types_db:
            product_types.add(InlineKeyboardButton(text=type[1], callback_data=str(type[0])))
        return product_types.adjust(2).as_markup()
    else:
        return None

async def get_product_types_to_del():
    product_types_db = await db.get_product_types()
    product_types = InlineKeyboardBuilder()
    for type in product_types_db:
        product_types.add(InlineKeyboardButton(text=type[1], callback_data=str(type[0])))
    product_types.add(InlineKeyboardButton(text="🔙 Oynani yopish", callback_data='back'))
    return product_types.adjust(2).as_markup()

product_save_button = InlineKeyboardBuilder(
    markup=[
        [
            InlineKeyboardButton(text="✅ Saqlash", callback_data='save_product'),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data='cancel_product')
        ]
    ]
).adjust(2).as_markup()
