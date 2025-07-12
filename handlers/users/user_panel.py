from aiogram import types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from keyboards.default import user_keyboard
from keyboards.inline import get_orders, user_order_keyboard
from loader import dp, db


@dp.message(lambda message: message.text == '🛒 Mahsulotlarni ko\'rish')
async def send_orders(msg: types.Message, state: FSMContext):
    await msg.answer("Mahsulotlar ro'yxati", reply_markup=await get_orders(msg.from_user.id))
    await state.set_state('get_order')


@dp.callback_query(StateFilter('get_order'), F.data == 'back')
async def send_order_info(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Bosh menyu", reply_markup=user_keyboard)
    await state.clear()


@dp.callback_query(StateFilter('get_order'), F.data.isdigit())
async def send_order_info(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.update_data(order_id=call.data)
    await order_info(call, state, call.data)



@dp.callback_query(StateFilter('order_info'), F.data)
async def send_order_info(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    if call.data == 'back':
        await call.message.answer("Mahsulotlar ro'yxati", reply_markup=await get_orders(call.from_user.id))
        await state.set_state('get_order')
        return
    elif call.data == 'get_payment_info':
        order_id = (await state.get_data()).get('order_id')
        order_data = await db.get_payment_info(order_id)
        info = (
            "📦 <b>Mahsulot ma’lumotlari:</b>\n\n"
            f"📦 <b>Mahsulot nomi:</b> {order_data[0][0]}\n"
            f"💳 <b>Umumiy qarz:</b> {order_data[-1][1]}$\n"
            f"📤 <b>Oylik to‘lov:</b> {order_data[-1][2]}$\n"
            f"📅 <b>To'lo'v sanasi:</b>\n"
        )
        for i in range(len(order_data)):
            if order_data[i][4]:
                info += (
                    f"✅ {order_data[i][3]}\n"
                )
                continue
            info += (
                f"{order_data[i][3]}\n"
            )
        await call.message.answer(info)

    else:
        await call.message.answer("Tugmachalardan birini tanlang!!")





async def order_info(call, state, order_id):
    order_data = await db.get_order_by_id(order_id)
    info = (
        "📦 <b>Mahsulot ma’lumotlari:</b>\n\n"
        f"👤 <b>Ism:</b> {order_data[1]}\n"
        f"📞 <b>Telefon:</b> {order_data[2]}\n"
        f"📦 <b>Mahsulot nomi:</b> {order_data[4]}\n"
        f"🏷️ <b>Turi:</b> {order_data[3]}\n"
        f"📅 <b>Yil:</b> {order_data[5]}\n"
        f"📆 <b>To‘lov muddati:</b> {order_data[9]} oy\n"
        f"🗓 <b>To‘lov kuni:</b> {order_data[10]}\n"
    )
    if order_data[11]:
        info += f"💸 <b>Boshlang‘ich to‘lov:</b> {order_data[11]}$\n"
    info += (
        f"💳 <b>Umumiy qarz:</b> {order_data[8]}$\n"
        f"📤 <b>Oylik to‘lov:</b> {order_data[12]}$\n"
        f"📅 <b>Olingan sana:</b> {order_data[14]}"
    )
    await call.message.answer(info, reply_markup=user_order_keyboard)
    await state.set_state('order_info')




