import asyncio

from aiogram import types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from keyboards.inline import (
    add_info_button, get_user_orders, order_keyboards, order_save_button
)
from loader import dp, db, bot
from states.orderStates import OrderEditState


@dp.callback_query(F.data == "edit_info")
async def edit_order(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Mahsulotni o'zgartirish uchun kreditga tegishli"
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


@dp.callback_query(StateFilter(OrderEditState.access_payment), F.data)
async def handle_payment_type(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    wait_msg = await call.message.answer("Kutib turing...")
    await asyncio.sleep(2)

    data = await state.get_data()
    product_id = data['product_id']

    payment_info = await db.get_per_month_payment(product_id)
    if not payment_info:
        await call.message.answer("To'lov ma'lumotlari topilmadi.")
        await state.clear()
        return

    payment_sum = payment_info[0]

    prev_payment = await db.get_previous_payment(product_id)
    await wait_msg.delete()
    await state.update_data(payment_date=prev_payment[3])

    if call.data == 'part_payment':
        if prev_payment and not prev_payment[2] and prev_payment[1] != payment_sum:
            await call.message.answer(
                f"Siz oldingi oy uchun to'liq to'lov qilmagansiz.\n"
                f"Oldingi oy uchun to'lovni kiriting {prev_payment[1]}$:"
            )
            await state.set_state(OrderEditState.debt_price)
            return

        elif payment_sum > 0:
            await call.message.answer(
                f"Siz {payment_sum}$ gacha qisman to'lov qilishingiz mumkin.\n"
                "Iltimos, to'lov summasini kiriting ($):"
            )
            await state.set_state(OrderEditState.part_sum)
        else:
            await call.message.answer("To'lov summasi noto'g'ri yoki to'lov qilinib bo'lgan.")
            await state.clear()

    elif call.data == 'monthly_payment':
        if prev_payment and not prev_payment[2] and prev_payment[1] != payment_sum:
            await call.message.answer(
                "Siz oldingi oy uchun to'liq to'lov qilmagansiz.\n"
                "Iltimos, oldingi oy uchun to'lovni to'liq qiling!",
                reply_markup=order_keyboards
            )
            return

        await call.message.answer(
            f"Oylik to'lov summasini kiriting {payment_sum}$:"
        )
        await state.set_state(OrderEditState.debt_price_monthly)
    elif call.data == 'full_payment':
        await call.message.answer("To'lovni tasdiqlang.", reply_markup=order_save_button)
        await state.set_state(OrderEditState.access_edit)



@dp.message(OrderEditState.part_sum)
async def process_part_payment(msg: types.Message, state: FSMContext):
    text = msg.text.strip()
    if not text.isdigit():
        await msg.answer("Iltimos, faqat raqam kiriting.")
        return

    pay_amount = float(text)
    data = await state.get_data()
    product_id = data['product_id']

    payment_info = await db.get_per_month_payment(product_id)
    if not payment_info:
        await msg.answer("To'lov ma'lumotlari topilmadi.")
        await state.clear()
        return

    payment_sum = payment_info[0]

    if pay_amount <= 0 or pay_amount > payment_sum:
        await msg.answer(f"To'lov summasi 0 dan katta va {payment_sum}$ dan oshmasligi kerak.")
        return

    await state.update_data(part_debt=pay_amount)
    await msg.answer("To'lovni tasdiqlang.", reply_markup=order_save_button)
    await state.set_state(OrderEditState.access_edit)


@dp.message(OrderEditState.debt_price)
async def process_debt_price(msg: types.Message, state: FSMContext):
    text = msg.text.strip()
    if not text.isdigit():
        await msg.answer("Iltimos, faqat raqam kiriting.")
        return

    pay_amount = float(text)
    data = await state.get_data()
    product_id = data['product_id']

    payment_info = await db.get_previous_payment(product_id)
    if not payment_info:
        await msg.answer("To'lov ma'lumotlari topilmadi.")
        await state.clear()
        return

    payment_sum = payment_info[1]

    if pay_amount != payment_sum:
        await msg.answer(f"To'lov summasi aniq {payment_sum}$ bo'lishi kerak.")
        return

    await state.update_data(monthly_debt=pay_amount)
    await state.update_data(payment_date=payment_info[3])
    await msg.answer("To'lovni tasdiqlang.", reply_markup=order_save_button)
    await state.set_state(OrderEditState.access_edit)


@dp.message(OrderEditState.debt_price_monthly)
async def process_monthly_payment(msg: types.Message, state: FSMContext):
    text = msg.text.strip()
    if not text.isdigit():
        await msg.answer("Iltimos, faqat raqam kiriting.")
        return

    pay_amount = float(text)
    data = await state.get_data()
    product_id = data['product_id']

    payment_info = await db.get_per_month_payment(product_id)
    if not payment_info:
        await msg.answer("To'lov ma'lumotlari topilmadi.")
        await state.clear()
        return

    payment_sum = payment_info[0]

    if pay_amount != payment_sum:
        await msg.answer(f"To'lov summasi aniq {payment_sum}$ bo'lishi kerak.")
        return

    await state.update_data(monthly_debt=pay_amount)
    await msg.answer("To'lovni tasdiqlang.", reply_markup=order_save_button)
    await state.set_state(OrderEditState.access_edit)


@dp.callback_query(OrderEditState.access_edit, F.data == 'save_product')
async def save_order(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    sek_msg = await call.message.answer("⏳ Bir necha sekund kutib turing.")
    data = await state.get_data()
    pr_id = data['product_id']

    pay_amount = 0
    if 'part_debt' in data:
        pay_amount = float(data['part_debt'])
    elif 'monthly_debt' in data:
        pay_amount = float(data['monthly_debt'])
    else:
        order_data = await db.get_order_by_id(pr_id)
        if order_data:
            pay_amount = float(order_data[8])

    success = await db.update_order_by_id(pr_id, pay_amount)
    if not success:
        await sek_msg.delete()
        await call.message.answer("❌ To'lovni saqlashda xatolik yuz berdi.")
        await state.clear()
        return

    if 'part_debt' in data:
        await db.update_payment_sum(order_id=pr_id, payment_sum=pay_amount, payment_date=data['payment_date'])
    elif 'monthly_debt' in data:
        await db.update_payment_sum(order_id=pr_id, payment_sum=pay_amount, payment_date=data['payment_date'], month_payment=True)
    else:
        await db.update_payment_sum(order_id=pr_id, payment_sum=pay_amount, full_payment=True)

    user_info = await db.get_user_by_number(data['phone_number'])
    if user_info[4]:
        await bot.send_message(chat_id=int(user_info[4]), text = f"✅ Sizning buyurtmangiz uchun {pay_amount}$ muvaffaqiyatli to'landi")
    await sek_msg.delete()
    await call.message.answer("✅ Ma'lumotlar muvaffaqiyatli tarzda o'zgartirildi.", reply_markup=add_info_button)
    await state.clear()



@dp.callback_query(OrderEditState.access_edit, F.data == 'cancel_product')
async def back_to_menu(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("‼️ Ma'lumot o'zgartirilmadi", reply_markup=add_info_button)
    await state.clear()
