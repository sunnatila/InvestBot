from aiogram import types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from keyboards.inline import (
    add_info_button, get_user_orders, order_keyboards, order_save_button
)
from loader import dp, db
from states.orderStates import OrderEditState


@dp.callback_query(F.data == "edit_info")
async def edit_order(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Mahsulotni o'zgartirish uchun mahsulotga tegishli"
                              " telefon raqamini kiriting (+998 xx xxx xx xx) :"
                              )
    await state.set_state(OrderEditState.phone_number)


@dp.message(StateFilter(OrderEditState.phone_number))
async def get_user_name(msg: types.Message, state: FSMContext):
    number = msg.text.strip()
    if number.startswith('+998') and len(number) == 13:
        pass
    elif number.isdigit() and len(number) == 9:
        number = '+998' + number
    else:
        await msg.answer("❌ Telefon raqam noto'g'ri. Qayta kiriting.")
        return
    access_number = await db.get_orders_by_phone(number)
    if access_number:
        await msg.answer("Qaysi mahsulotni o'zgartirmoqchisiz?", reply_markup=await get_user_orders(number))
        await state.update_data(phone_number=number)
        await state.set_state(OrderEditState.product_id)
    else:
        await msg.answer("❌ Bunday telefon raqamga tegishli mahsulotlar mavjud emas.", reply_markup=add_info_button)
        await state.clear()


@dp.callback_query(StateFilter(OrderEditState.product_id), F.data.isdigit())
async def get_product_id(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    product_id = call.data
    await state.update_data(product_id=product_id)
    data = await db.get_order_by_id(product_id)
    info = (
        "📦 <b>Mahsulot ma’lumotlari:</b>\n\n"
        f"👤 <b>Ism:</b> {data[1]}\n"
        f"📞 <b>Telefon:</b> {data[2]}\n"
        f"📦 <b>Mahsulot nomi:</b> {data[4]}\n"
        f"🏷️ <b>Turi:</b> {data[3]}\n"
        f"📅 <b>Yil:</b> {data[5]}\n"
        f"💵 <b>Narx:</b> {data[6]}$\n"
        f"📈 <b>Foiz:</b> {data[7]}%\n"
        f"📆 <b>To‘lov muddati:</b> {data[9]} oy\n"
        f"🗓 <b>To‘lov kuni:</b> {data[10]}\n"
    )
    if data[11]:
        info += f"💸 <b>Boshlang‘ich to‘lov:</b> {data[11]}$\n"
    info += (
        f"💳 <b>Umumiy qarz:</b> {data[8]}$\n"
        f"📤 <b>Oylik to‘lov:</b> {data[12]}$\n"
        f"📊 <b>Foyda:</b> {data[13]}$\n"
        f"📅 <b>Sana:</b> {data[14]}"
    )
    await call.message.answer(info, reply_markup=order_keyboards)
    await state.set_state(OrderEditState.access_payment)


@dp.callback_query(StateFilter(OrderEditState.product_id), F.data == 'back')
async def back_to_home(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Bosh menyu", reply_markup=add_info_button)
    await state.clear()


@dp.callback_query(StateFilter(OrderEditState.access_payment), F.data == "back")
async def get_debt_price(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    data = await state.get_data()
    number = data['phone_number']
    await call.message.answer("Qaysi mahsulotni o'zgartirmoqchisiz?", reply_markup=await get_user_orders(number))
    await state.set_state(OrderEditState.product_id)


@dp.callback_query(StateFilter(OrderEditState.access_payment), F.data == "payment")
async def get_debt_price(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("To'lo'v miqdorini kiriting ($):")
    await state.set_state(OrderEditState.debt_price)


@dp.message(OrderEditState.debt_price, F.text.isdigit())
async def get_debt_price(msg: types.Message, state: FSMContext):
    debt_price = msg.text
    await state.update_data(debt_price=debt_price)
    await msg.answer("To'lo'vni tasdiqlang.", reply_markup=order_save_button)
    await state.set_state(OrderEditState.access_edit)


@dp.callback_query(OrderEditState.access_edit, F.data == 'save_product')
async def save_order(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    pr_id = data['product_id']
    debt_price = data['debt_price']
    await db.update_order_by_id(pr_id, debt_price)
    await call.message.delete()
    await call.message.answer("✅ Ma'lumotlar muvaffaqiyatli tarzda o'zgartirildi.", reply_markup=add_info_button)
    await state.clear()


@dp.callback_query(OrderEditState.access_edit, F.data == 'cancel_product')
async def back_to_menu(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("‼️ Ma'lumot o'zgartirilmadi", reply_markup=add_info_button)
    await state.clear()
