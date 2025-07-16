from datetime import datetime
from typing import Dict, Any, Optional
from aiogram import types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards.inline import (
    add_info_button, get_product_types,
    product_first_payment, product_save_button, add_order_button, get_users
)
from loader import dp, db
from states.orderStates import OrderStates
from utils.sheets_panel import add_order_to_sheets_async
import asyncio


class ErrorMessages:
    INVALID_PHONE = "❌ Telefon raqam noto'g'ri. +998XXXXXXXXX yoki 9XXXXXXXX formatida kiriting."
    INVALID_YEAR = "❌ Yil noto'g'ri. 2015-{current_year} oralig'ida bo'lishi kerak."
    INVALID_PRICE = "❌ Narx noto'g'ri. Musbat son kiriting."
    INVALID_PERCENTAGE = "❌ Foiz 0-100% oralig'ida bo'lishi kerak."
    INVALID_DEBT_TERM = "❌ Muddat 1-60 oy oralig'ida bo'lishi kerak."
    INVALID_DAY = "❌ Kun noto'g'ri. 1-31 oralig'ida bo'lishi kerak."
    PAYMENT_TOO_HIGH = "‼️ Boshlang'ich to'lov tan narxidan katta.\nQaytadan kiriting."
    INVALID_PRODUCT_TYPE = "❌ Mahsulot turini faqat hariflarda kiriting"


class Validators:
    @staticmethod
    def format_phone(number: str) -> Optional[str]:
        if not number:
            return None
            
        number = number.strip().replace(' ', '')
        if number.startswith('+998') and len(number) == 13 and number[1:].isdigit():
            return number
        elif number.isdigit() and len(number) == 9:
            return f'+998{number}'
        elif number.isdigit() and len(number) == 12 and number.startswith('998'):
            return f'+{number}'
        return None

    @staticmethod
    def is_valid_year(year: str) -> bool:
        if not year or not year.isdigit():
            return False
        current_year = datetime.now().year
        return 2015 <= int(year) <= current_year

    @staticmethod
    def is_valid_price(price: str) -> bool:
        try:
            return float(price) >= 0
        except (ValueError, TypeError):
            return False

    @staticmethod
    def is_valid_percentage(percent: str) -> bool:
        try:
            return 0 <= float(percent) <= 100
        except (ValueError, TypeError):
            return False

    @staticmethod
    def is_valid_debt_term(term: str) -> bool:
        return term.isdigit() and 1 <= int(term) <= 60

    @staticmethod
    def is_valid_payment_day(day: str) -> bool:
        return day.isdigit() and 1 <= int(day) <= 31


validator = Validators()


# ------------------------ Initial Step ------------------------
@dp.callback_query(F.data == 'add_credit')
async def add_info(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("F.I.Sh kiriting:")
    await state.set_state(OrderStates.user_name)



@dp.callback_query(F.data == 'add_credit_to_existing_client')
async def add_info(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Qaysi mijozga qo'shimcha kredit qo'shmoqchisiz:", reply_markup=await get_users())
    await state.set_state("get_client")


@dp.callback_query(StateFilter('get_client'), F.data)
async def add_info(call: CallbackQuery, state: FSMContext):
    if call.data == 'back':
        await call.message.delete()
        await call.message.answer("Bosh menyu:", reply_markup=add_info_button)
        await state.clear()
        return
    user_info = await db.get_user_by_tg_id(user_id=call.data)
    user_name = user_info[1]
    number = user_info[2]
    await state.update_data(user_name=user_name, number=number)
    await call.message.delete()
    await call.message.answer("Mahsulot nomini kiriting:")
    await state.set_state(OrderStates.product_name)


# ------------------------ Step-by-step Data Collection ------------------------
@dp.message(StateFilter(OrderStates.user_name))
async def get_user_name(msg: types.Message, state: FSMContext):
    await state.update_data(user_name=msg.text)
    await msg.answer("Telefon raqam kiriting: (+998901234567 yoki 901234567)")
    await state.set_state(OrderStates.phone_number)


async def _get_phone_validation_result(number: str) -> tuple[bool, Optional[Dict[str, Any]]]:
    formatted_number = validator.format_phone(number)
    if not formatted_number:
        return False, None
        
    user_info = await db.get_user_by_number(formatted_number)
    return True, user_info


@dp.message(StateFilter(OrderStates.phone_number))
async def get_phone(msg: types.Message, state: FSMContext):
    is_valid, user_info = await _get_phone_validation_result(msg.text)
    
    if not is_valid:
        await msg.answer(ErrorMessages.INVALID_PHONE)
        return
    if user_info:
        await state.update_data(
            user_name=user_info[1],
            number=user_info[2],
        )
        await msg.answer(
            "ℹ️ Bu telefon raqamli mijoz mavjud.\n"
            "Manashu mijozga kredit qo'shishni xohlaysizmi?",
            reply_markup=add_order_button
        )
        await state.set_state('add_order_to_user')
        return
        
    await state.update_data(number=validator.format_phone(msg.text))
    await msg.answer("Mahsulot nomini kiriting:")
    await state.set_state(OrderStates.product_name)


@dp.callback_query(StateFilter('add_order_to_user'), F.data == 'add_order')
async def add_order_to_user(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Mahsulot nomini kiriting:")
    await state.set_state(OrderStates.product_name)


@dp.callback_query(StateFilter('add_order_to_user'), F.data == 'cancel_order')
async def cancel_order(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Bosh menyu", reply_markup=add_info_button)
    await state.clear()


@dp.message(StateFilter(OrderStates.product_name))
async def get_product_name(msg: types.Message, state: FSMContext):
    await state.update_data(product_name=msg.text)
    pr_types = await get_product_types()
    if pr_types:
        await msg.answer("Mahsulot turini tanlang:", reply_markup=pr_types)
    else:
        await msg.answer("Mahsulot turini kiriting:")
    await state.set_state(OrderStates.product_type)


@dp.callback_query(StateFilter(OrderStates.product_type), F.data.isdigit())
async def get_product_type(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.update_data(product_type=int(call.data))
    await call.message.answer("Mahsulot yilini kiriting (masalan: 2023):")
    await state.set_state(OrderStates.product_year)


@dp.callback_query(StateFilter(OrderStates.product_type), F.data == 'add_another')
async def add_another_type(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Mahsulot turini kiriting:")


@dp.message(StateFilter(OrderStates.product_type))
async def get_pr_type(msg: types.Message, state: FSMContext):
    if msg.text.isalpha():
        await db.add_product_type(msg.text)
        pr_type = await db.get_product_type_by_name(msg.text)
        await state.update_data(product_type=int(pr_type[0]))
        await msg.answer("Mahsulot yilini kiriting (masalan: 2023):")
        await state.set_state(OrderStates.product_year)
    else:
        await msg.answer("Mahsulot turini faqat hariflarda kiriting ‼️")


@dp.message(StateFilter(OrderStates.product_year))
async def get_product_year(msg: Message, state: FSMContext):
    if not validator.is_valid_year(msg.text):
        current_year = datetime.now().year
        await msg.answer(ErrorMessages.INVALID_YEAR.format(current_year=current_year))
        return
        
    await state.update_data(product_year=int(msg.text))
    await msg.answer("Mahsulot narxini kiriting ($):")
    await state.set_state(OrderStates.product_price)


@dp.message(StateFilter(OrderStates.product_price))
async def get_product_price(msg: Message, state: FSMContext):
    if not validator.is_valid_price(msg.text):
        await msg.answer(ErrorMessages.INVALID_PRICE)
        return
        
    await state.update_data(product_price=float(msg.text))
    await msg.answer(
        "Boshlang'ich to'lo'v mavjudmi?",
        reply_markup=product_first_payment
    )
    await state.set_state(OrderStates.access_first_payment)


@dp.callback_query(StateFilter(OrderStates.access_first_payment), F.data == "yes")
async def access_first_payment_yes(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Boshlang'ich to'lo'vni kiriting ($):")
    await state.set_state(OrderStates.first_payment)


@dp.callback_query(StateFilter(OrderStates.access_first_payment), F.data == "no")
async def access_first_payment_no(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.update_data(first_payment=0)
    await call.message.answer("Foiz stavkasini kiriting (%):")
    await state.set_state(OrderStates.product_percentage)


@dp.message(StateFilter(OrderStates.first_payment))
async def get_first_payment(msg: types.Message, state: FSMContext):
    if not validator.is_valid_price(msg.text):
        await msg.answer(ErrorMessages.INVALID_PRICE)
        return
        
    data = await state.get_data()
    first_payment = float(msg.text)
    
    if first_payment > float(data['product_price']):
        await msg.answer(ErrorMessages.PAYMENT_TOO_HIGH)
        return
        
    await state.update_data(first_payment=first_payment)
    await msg.answer("Foiz stavkasini kiriting (%):")
    await state.set_state(OrderStates.product_percentage)


@dp.message(StateFilter(OrderStates.product_percentage))
async def get_percentage(msg: Message, state: FSMContext):
    if not validator.is_valid_percentage(msg.text):
        await msg.answer(ErrorMessages.INVALID_PERCENTAGE)
        return
        
    await state.update_data(product_percentage=float(msg.text))
    await msg.answer("To'lo'v muddatini kiriting (1-60 oy):")
    await state.set_state(OrderStates.debt_term)


@dp.message(StateFilter(OrderStates.debt_term))
async def get_debt_term(msg: Message, state: FSMContext):
    if not validator.is_valid_debt_term(msg.text):
        await msg.answer(ErrorMessages.INVALID_DEBT_TERM)
        return
        
    await state.update_data(debt_term=int(msg.text))
    await msg.answer("To'lo'v kunini kiriting (1-31):")
    await state.set_state(OrderStates.payment_date)


@dp.message(StateFilter(OrderStates.payment_date))
async def get_payment_date(msg: Message, state: FSMContext):
    if not validator.is_valid_payment_day(msg.text):
        await msg.answer(ErrorMessages.INVALID_DAY)
        return
        
    await state.update_data(payment_date=int(msg.text))
    await send_order_info(msg, state)
    await state.set_state(OrderStates.order_access)


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
    sek_msg = await call.message.answer("⏳ Bir necha sekund kutib turing...")
    data = await state.get_data()
    await db.add_order(
        data['user_name'], data['number'], data['product_name'],
        data['product_year'], data['product_type'], float(data['product_price']),
        float(data['product_percentage']), int(data['debt_term']),
        int(data['payment_date']), float(data.get('first_payment', 0))
    )
    count = await db._execute("SELECT COUNT(id) FROM orders", fetchone=True)
    order_id = count[0] if count else None

    if order_id:
        asyncio.create_task(add_order_to_sheets_async(db, order_id))
    await asyncio.sleep(2)
    await sek_msg.delete()
    await call.message.answer("✅ Mahsulot muvaffaqiyatli qo'shildi.", reply_markup=add_info_button)
    await state.clear()


@dp.callback_query(OrderStates.order_access, F.data == 'cancel_product')
async def cancel_product(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("‼️ Mahsulot saqlanmadi.", reply_markup=add_info_button)
    await state.clear()
