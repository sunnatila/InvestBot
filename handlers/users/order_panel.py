
from datetime import datetime
from aiogram import types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from keyboards.inline import (
    add_info_button, get_product_types,
    product_first_payment, product_save_button
)
from loader import dp, db
from states.orderStates import OrderStates

# ------------------------ Initial Step ------------------------
@dp.callback_query(F.data == 'add_info')
async def add_info(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    pr_types = await get_product_types()
    if pr_types:
        await call.message.answer("F.I.Sh kiriting:")
        await state.set_state(OrderStates.user_name)
    else:
        await call.message.answer("Mahsulot turi mavjud emas!\nBirinchi turini qo‘shing!", reply_markup=add_info_button)
        await state.clear()

# ------------------------ Step-by-step Data Collection ------------------------
@dp.message(StateFilter(OrderStates.user_name))
async def get_user_name(msg: types.Message, state: FSMContext):
    await state.update_data(user_name=msg.text)
    await msg.answer("Telefon raqam kiriting: (+998901234567 yoki 901234567)")
    await state.set_state(OrderStates.phone_number)

@dp.message(StateFilter(OrderStates.phone_number))
async def get_phone(msg: types.Message, state: FSMContext):
    number = msg.text.strip()
    if number.startswith('+998') and len(number) == 13:
        pass
    elif number.isdigit() and len(number) == 9:
        number = '+998' + number
    else:
        await msg.answer("❌ Telefon raqam noto‘g‘ri. Qayta kiriting.")
        return
    await state.update_data(number=number)
    await msg.answer("Mahsulot nomini kiriting:")
    await state.set_state(OrderStates.product_name)

@dp.message(StateFilter(OrderStates.product_name))
async def get_product_name(msg: types.Message, state: FSMContext):
    await state.update_data(product_name=msg.text)
    await msg.answer("Mahsulot turini tanlang:", reply_markup=await get_product_types())
    await state.set_state(OrderStates.product_type)

@dp.callback_query(StateFilter(OrderStates.product_type), F.data.isdigit())
async def get_product_type(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.update_data(product_type=int(call.data))
    await call.message.answer("Mahsulot yilini kiriting (masalan: 2023):")
    await state.set_state(OrderStates.product_year)

@dp.message(StateFilter(OrderStates.product_year))
async def get_product_year(msg: types.Message, state: FSMContext):
    if msg.text.isdigit() and 2015 <= int(msg.text) <= datetime.now().year:
        await state.update_data(product_year=int(msg.text))
        await msg.answer("Mahsulot narxini kiriting ($):")
        await state.set_state(OrderStates.product_price)
    else:
        await msg.answer("❌ Yil noto‘g‘ri. Qayta kiriting.")

@dp.message(StateFilter(OrderStates.product_price))
async def get_product_price(msg: types.Message, state: FSMContext):
    if msg.text.isdigit():
        await state.update_data(product_price=float(msg.text))
        await msg.answer("Boshlang‘ich to‘lov mavjudmi?", reply_markup=product_first_payment)
        await state.set_state(OrderStates.access_first_payment)
    else:
        await msg.answer("❌ Narx noto‘g‘ri. Qayta kiriting.")

@dp.callback_query(StateFilter(OrderStates.access_first_payment), F.data == "yes")
async def access_first_payment_yes(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Boshlang‘ich to‘lovni kiriting ($):")
    await state.set_state(OrderStates.first_payment)

@dp.callback_query(StateFilter(OrderStates.access_first_payment), F.data == "no")
async def access_first_payment_no(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.update_data(first_payment=0)
    await call.message.answer("Foiz stavkasini kiriting (%):")
    await state.set_state(OrderStates.product_percentage)

@dp.message(StateFilter(OrderStates.first_payment))
async def get_first_payment(msg: types.Message, state: FSMContext):
    if msg.text.isdigit():
        data = await state.get_data()
        if float(msg.text) <= float(data['product_price']):
            await state.update_data(first_payment=float(msg.text))
            await msg.answer("Foiz stavkasini kiriting (%):")
            await state.set_state(OrderStates.product_percentage)
        else:
            await msg.answer("‼️ Boshlang'ich to'lo'v tan narxidan katta.\nQaytadan kiriting.")
    else:
        await msg.answer("❌ Narx noto‘g‘ri. Qayta kiriting.")

@dp.message(StateFilter(OrderStates.product_percentage))
async def get_percentage(msg: types.Message, state: FSMContext):
    if msg.text.isdigit():
        await state.update_data(product_percentage=float(msg.text))
        await msg.answer("To‘lov muddatini kiriting (oy):")
        await state.set_state(OrderStates.debt_term)
    else:
        await msg.answer("❌ Foiz noto‘g‘ri. Qayta kiriting.")

@dp.message(StateFilter(OrderStates.debt_term))
async def get_debt_term(msg: types.Message, state: FSMContext):
    if msg.text.isdigit() and 1 <= int(msg.text) <= 60:
        await state.update_data(debt_term=int(msg.text))
        await msg.answer("To‘lov kunini kiriting (1–31):")
        await state.set_state(OrderStates.payment_date)
    else:
        await msg.answer("❌ Muddat noto‘g‘ri. Qayta kiriting.")

@dp.message(StateFilter(OrderStates.payment_date))
async def get_payment_date(msg: types.Message, state: FSMContext):
    if msg.text.isdigit() and 1 <= int(msg.text) <= 31:
        await state.update_data(payment_date=int(msg.text))
        await send_order_info(msg, state)
        await state.set_state(OrderStates.order_access)
    else:
        await msg.answer("❌ Kun noto‘g‘ri. 1–31 oralig‘ida kiriting.")

# ------------------------ Confirmation Step ------------------------
async def send_order_info(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    pr_price = float(data["product_price"])
    pr_percent = float(data["product_percentage"])
    first_pay = float(data.get("first_payment", 0))
    debt_term = int(data["debt_term"])

    benefit = round((pr_price - first_pay) * pr_percent / 100) if first_pay else round(pr_price * pr_percent / 100)
    total_debt = (pr_price - first_pay + benefit) if first_pay else (pr_price + benefit)
    per_month = round(total_debt / debt_term)
    pr_type = await db.get_product_type(data["product_type"])

    info = (
        f"📦 <b>Mahsulot ma’lumotlari:</b>\n\n"
        f"👤 <b>Ism:</b> {data['user_name']}\n"
        f"📞 <b>Telefon:</b> {data['number']}\n"
        f"📦 <b>Mahsulot nomi:</b> {data['product_name']}\n"
        f"🏷️ <b>Turi:</b> {pr_type[1]}\n"
        f"📅 <b>Yil:</b> {data['product_year']}\n"
        f"💵 <b>Narx:</b> {pr_price}$\n"
        f"📈 <b>Foiz:</b> {pr_percent}%\n"
        f"📆 <b>To‘lov muddati:</b> {debt_term} oy\n"
        f"🗓 <b>To‘lov kuni:</b> {data['payment_date']}\n"
    )
    if first_pay:
        info += f"💸 <b>Boshlang‘ich to‘lov:</b> {first_pay}$\n"
    info += (
        f"💳 <b>Umumiy qarz:</b> {total_debt}$\n"
        f"📤 <b>Oylik to‘lov:</b> {per_month}$\n"
        f"📊 <b>Foyda:</b> {benefit}$\n"
        f"📅 <b>Sana:</b> {datetime.today().date()}"
    )
    await msg.answer(info, reply_markup=product_save_button)

# ------------------------ Save or Cancel ------------------------
@dp.callback_query(OrderStates.order_access, F.data == 'save_product')
async def save_product(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    sek_msg = await call.message.answer("⏳ Bir necha sekund kutib turing.")
    data = await state.get_data()
    await db.add_order(
        data['user_name'], data['number'], data['product_name'],
        data['product_year'], data['product_type'], float(data['product_price']),
        float(data['product_percentage']), int(data['debt_term']),
        int(data['payment_date']), float(data.get('first_payment', 0))
    )
    await sek_msg.delete()
    await call.message.answer("✅ Mahsulot muvaffaqiyatli qo'shildi.", reply_markup=add_info_button)
    await state.clear()

@dp.callback_query(OrderStates.order_access, F.data == 'cancel_product')
async def cancel_product(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("‼️ Mahsulot saqlanmadi.", reply_markup=add_info_button)
    await state.clear()
