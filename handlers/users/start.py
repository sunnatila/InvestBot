from aiogram import types
from aiogram.filters import CommandStart, BaseFilter, StateFilter
from aiogram.fsm.context import FSMContext

from data.config import ADMINS
from keyboards.default import user_keyboard
from keyboards.inline import add_info_button
from loader import dp, db


def format_phone(number: str) -> str | None:
    number = number.strip()
    if number.startswith('+998') and len(number) == 13 and number[1:].isdigit():
        return number
    elif number.isdigit() and len(number) == 9:
        return '+998' + number
    return None


class AdminFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return str(message.from_user.id) in ADMINS


@dp.message(CommandStart(), AdminFilter())
async def bot_start(message: types.Message):
    await message.answer(f"Assalomu Alaykum.\n"
                         f"Admin panelga xush kelibsiz.", reply_markup=add_info_button)


@dp.message(CommandStart())
async def bot_start(message: types.Message, state: FSMContext):
    user_info = await db.get_user_by_tg_id(message.from_user.id)
    if user_info:
        await message.answer("Bosh menyu.", reply_markup=user_keyboard)
        return
    await message.answer(f"Assalomu Alaykum.\n"
                         f"Invest botiga xush kelibsiz.\n"
                         f"Botdan foydalanish uchun telefon raqamingizni kiriting. (+998901234567 yoki 901234567)"
                         )
    await state.set_state("phone_number")

@dp.message(StateFilter("phone_number"))
async def get_user_name(msg: types.Message, state: FSMContext):
    number = format_phone(msg.text)
    if not number:
        await msg.answer("❌ Telefon raqam noto‘g‘ri. Qayta kiriting.")
        return
    access_number = await db.get_user_by_number(number)
    if access_number:
        if access_number[3]:
            await msg.answer("‼️ Bu telefon raqamli foydalanuvchi botdan foydalanmoqda.")
            await state.clear()
            return
        await db.update_user_info(number, tg_id=msg.from_user.id)
        await msg.answer("✅ Botdan foydalanishingiz mumkin.", reply_markup=user_keyboard)
        await state.clear()
    else:
        await msg.answer("❌ Bunday telefon raqamga tegishli ma'lumotlar mavjud emas.")
        await state.clear()

