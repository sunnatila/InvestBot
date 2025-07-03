from aiogram import F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from keyboards.inline import product_keyboard, get_product_types_to_del
from keyboards.inline import add_info_button
from loader import dp, db

@dp.callback_query(F.data == 'products')
async def add_info(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Tugmachalardan birini tanlang:", reply_markup=product_keyboard)
    await state.set_state("get_button")

@dp.callback_query(StateFilter("get_button"), F.data == 'add_pr_type')
async def add_product_type(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Mahsulot turini kiriting: ")
    await state.set_state("get_pr_type")

@dp.message(StateFilter("get_pr_type"))
async def get_product_type(msg: Message, state: FSMContext):
    product_type = msg.text
    await db.add_product_type(product_type)
    await msg.answer("✅ Mahsulot turi muvaffaqiyatli tarzda qo'shildi.", reply_markup=add_info_button)
    await state.clear()

@dp.callback_query(StateFilter("get_button"), F.data == 'del_pr_type')
async def del_product_type(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    if await db.get_product_types():
        await call.message.answer("Mahsulot turini tanlang: ", reply_markup=await get_product_types_to_del())
        await state.set_state("get_pr_type_to_del")
        return
    await call.message.answer("Mahsulot turlari mavjud emas!!", reply_markup=product_keyboard)
    await state.set_state("get_button")


@dp.callback_query(StateFilter("get_pr_type_to_del"), F.data.isdigit())
async def get_product_type_to_del(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    product_type = call.data
    await db.del_product_type(product_type)
    await call.message.answer("✅ Mahsulot turi muvaffaqiyatli tarzda o'chirildi.", reply_markup=add_info_button)
    await state.clear()

@dp.callback_query(StateFilter("get_pr_type_to_del"), F.data == 'back')
async def back(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Tugmachalardan birini tanlang:", reply_markup=product_keyboard)
    await state.set_state("get_button")


@dp.callback_query(StateFilter("get_button"), F.data == 'back')
async def back(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Bosh menyu", reply_markup=add_info_button)
    await state.clear()
